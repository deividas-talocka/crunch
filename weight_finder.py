"""Finds assessment weights in each module's Moodle content, by itself.

Lecturers put weights in different places: text on the Moodle page ("Assessment 1:
Professional Presentation (40%)"), an overview PDF ("CW 1 (Analysis) is worth 45% of
module mark"), or an assessment schedule ("Examination 70%"). This module reads those,
keeps the lines that look like weights, and matches them to the Moodle assessments.

The text-reading and matching functions are pure and tested; scan_course() does the
downloading; start() runs scans in the background so pages stay fast.
"""
import io
import re
import threading
import time

import requests
from pypdf import PdfReader

import moodle_client
import storage

PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s?%")
# Lines with these words are about pass marks, statistics or extra time, not weights.
NOISE = re.compile(
    r"pass mark|passed|failed|withdrew|resit|students|progressed|compensat|longer|"
    r"extra time|entitled|availab|attendance|similarity|discount",
    re.I,
)
COMBINED = re.compile(r"together|collectively|in total|combined|altogether|overall", re.I)
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]
MONTH = re.compile(r"\b(" + "|".join(MONTHS) + r")\b", re.I)
# (type, pattern) - the number after the word, if any, is group 1.
TYPES = [
    ("coursework", re.compile(r"\b(?:cw|coursework)\s*(\d+)?", re.I)),
    ("quiz", re.compile(r"\b(?:mcqs?|quiz(?:zes)?)\b\s*(\d+)?", re.I)),
    ("assessment", re.compile(r"\bassessment\s*(\d+)\b", re.I)),
    ("exam", re.compile(r"\b(?:exam|examination)s?\b()", re.I)),
    ("viva", re.compile(r"\bviva\b()", re.I)),
    ("presentation", re.compile(r"\bpresentation\b()", re.I)),
    ("tutorial", re.compile(r"\btutorials?\b()", re.I)),
]
RESCAN_AFTER = 24 * 3600
SCAN_VERSION = 2  # bump when the finder learns something new, so modules get re-read


def _kind_and_number(text):
    """The first assessment word in the text, e.g. ("coursework", 1) for "CW 1 (Analysis)"."""
    best = None
    for kind, pattern in TYPES:
        m = pattern.search(text)
        if m and (best is None or m.start() < best[0]):
            number = int(m.group(1)) if m.group(1) else None
            best = (m.start(), kind, number)
    return (best[1], best[2]) if best else (None, None)


def find_weights(text, source):
    """Weight findings in a block of text: [{kind, number, percent, combined, label, source}]."""
    findings = []
    lines = [line.strip() for line in text.splitlines()]
    for i, line in enumerate(lines):
        if NOISE.search(line):
            continue
        previous_end = 0
        for m in PERCENT.finditer(line):
            percent = float(m.group(1))
            context = line[previous_end:m.start()]
            previous_end = m.end()
            kind, number = _kind_and_number(context)
            if kind is None and i > 0 and not NOISE.search(lines[i - 1]):
                # Table layouts put the name on the line above: "Examination" / "70%".
                context = lines[i - 1] + " " + context
                kind, number = _kind_and_number(context)
            if kind is None or not 0 < percent <= 100:
                continue
            label = context.strip(" (:-–|•▪").strip() or kind.title()
            if len(label) > 80:
                label = "…" + label[-80:].split(" ", 1)[-1]  # keep whole words
            month = MONTH.search(context)
            findings.append({
                "kind": kind, "number": number, "percent": int(percent) if percent.is_integer() else percent,
                "combined": bool(COMBINED.search(context)), "label": label, "source": source,
                "month": MONTHS.index(month.group(1).lower()) + 1 if month else None,
            })
    return findings


def item_kind_and_number(name, kind):
    """Same idea for a Moodle assessment name; falls back to its Moodle type."""
    found_kind, number = _kind_and_number(name)
    if found_kind is None:
        found_kind = {"quiz": "quiz", "assign": "coursework", "exam": "exam"}.get(kind)
    return found_kind, number


def match(findings, items):
    """Pair findings with assessments. items: [{id, name, kind, ec}].
    Returns ({item_id: finding_used}, unmatched_findings)."""
    keyed = [(item, *item_kind_and_number(item["name"], item["kind"])) for item in items]
    counts = {}
    for item, kind, _ in keyed:
        if not item.get("ec"):
            counts[kind] = counts.get(kind, 0) + 1

    chosen, used = {}, set()
    for item, kind, number in keyed:
        best, best_rank = None, None
        for index, f in enumerate(findings):
            if f["kind"] != kind:
                continue
            if f["number"] is not None and number is not None and f["number"] != number:
                continue
            if f["number"] is not None and number is None:
                continue
            # Prefer: exact number > per-item figure > combined figure (split between items).
            if f["number"] is not None:
                rank = 0
            elif not f["combined"]:
                rank = 1 if (counts.get(kind, 0) == 1 or kind == "quiz") else None
            else:
                rank = 2
            if rank is not None and (best_rank is None or rank < best_rank):
                best, best_rank = (index, f), rank
        if best:
            index, f = best
            percent = f["percent"]
            if f["combined"] and counts.get(kind):
                percent = round(percent / counts[kind], 2)
            chosen[item["id"]] = {**f, "percent": percent}
            used.add(index)

    matched_kinds = {u["kind"] for u in chosen.values()}
    unmatched, seen = [], set()
    for index, f in enumerate(findings):
        key = (f["kind"], f["number"], f["percent"])
        if f["combined"] and f["kind"] in matched_kinds:
            continue  # e.g. "quizzes together worth 10%" once each quiz already has its weight
        if index not in used and key not in seen and not any(
            (u["kind"], u["number"], u["percent"]) == key for u in chosen.values()
        ):
            seen.add(key)
            unmatched.append(f)
    return chosen, unmatched


# --- Downloading -----------------------------------------------------------------

WANTED_FILE = re.compile(r"spec|overview|intro|schedule|assessment|handbook", re.I)
SKIPPED_FILE = re.compile(r"lecture\s*\d|tutorial|solution|answer|template|guidance|guideline|policy|L[1-9]\d*_", re.I)


def _html_text(html_text):
    return moodle_client._plain(html_text)


def scan_course(course_id):
    """All weight findings in one module's Moodle page text and selected PDFs."""
    _, token = moodle_client._settings()
    findings = []
    for section in moodle_client.call("core_course_get_contents", courseid=course_id):
        findings += find_weights(_html_text(section.get("summary")), "Moodle page")
        for mod in section.get("modules", []):
            findings += find_weights(_html_text(mod.get("description")), "Moodle page")
            for f in mod.get("contents") or []:
                label = f"{mod['name']} {f.get('filename', '')}"
                if (f.get("type") != "file" or not f.get("filename", "").lower().endswith(".pdf")
                        or not WANTED_FILE.search(label) or SKIPPED_FILE.search(label)
                        or f.get("filesize", 0) > 15_000_000):
                    continue
                try:
                    data = requests.get(f["fileurl"], params={"token": token}, timeout=60).content
                    pages = PdfReader(io.BytesIO(data)).pages[:40]
                    text = "\n".join(page.extract_text() or "" for page in pages)
                except Exception:
                    continue  # unreadable file: skip it
                findings += find_weights(text, f["filename"])
    return findings


# --- Running by itself in the background -------------------------------------------

_lock = threading.Lock()
_running = False


def is_running():
    return _running


def courses_needing_scan(modules, notes, now=None):
    """Modules never scanned, or with an unweighted assessment and no scan in the last day."""
    now = now or time.time()
    scans = notes.get("scans", {})
    due = []
    for module in modules:
        scan = scans.get(str(module["id"]))
        unweighted = any(r["weight"] is None for r in module["items"] if not r["ec"])
        if (scan is None or scan.get("version") != SCAN_VERSION
                or (unweighted and now - scan["at"] > RESCAN_AFTER)):
            due.append(module)
    return due


def exam_to_add(course_id, code, unmatched, existing_exams):
    """The exam to add for a module whose files mention one, or None if it already has an exam
    (added by me or earlier) or its files don't mention one."""
    exams = [f for f in unmatched if f["kind"] == "exam"]
    if not exams or any(e["course_id"] == course_id for e in existing_exams):
        return None
    f = max(exams, key=lambda e: e["percent"])
    return {
        "course_id": course_id, "name": f"{code} Exam", "close": None, "month": f.get("month"),
        "weight": f["percent"], "weight_source": f["source"], "auto": True, "done": False,
    }


def _apply(module, findings):
    """Save matched weights (never over one I typed), any exam the files mention,
    and the module's findings."""
    items = [{"id": r["id"], "name": r["name"], "kind": r["kind"], "ec": r["ec"]} for r in module["items"]]
    chosen, unmatched = match(findings, items)
    with storage.lock:
        notes = storage.load_notes()
        exam = exam_to_add(module["id"], module["code"], unmatched, notes["exams"])
        if exam:
            storage.add_found_exam(notes, exam)
            unmatched = [f for f in unmatched if f["kind"] != "exam"]
        for item_id, f in chosen.items():
            note = notes["assessments"].setdefault(item_id, {})
            typed_by_me = note.get("weight") is not None and not note.get("weight_source")
            if not typed_by_me:
                note["weight"] = f["percent"]
                note["weight_source"] = f["source"]
        notes.setdefault("scans", {})[str(module["id"])] = {
            "at": time.time(), "version": SCAN_VERSION, "unmatched": unmatched}
        storage.save_notes(notes)


def _run(modules):
    global _running
    try:
        for module in modules:
            try:
                _apply(module, scan_course(module["id"]))
            except moodle_client.MoodleError:
                pass  # offline or refused: try again on a later page load
    finally:
        _running = False


def start(modules):
    """Scan these modules in a background thread, unless a scan is already running."""
    global _running
    with _lock:
        if _running or not modules:
            return
        _running = True
    threading.Thread(target=_run, args=(modules,), daemon=True).start()
