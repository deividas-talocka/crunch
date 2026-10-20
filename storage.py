"""Reads and writes my notes (data/tracker.json). The data folder is gitignored."""
import json
import threading
from pathlib import Path

# The background weight finder and the web pages both save notes; this stops them
# overwriting each other's changes.
lock = threading.RLock()

DATA = Path(__file__).resolve().parent / "data"
NOTES = DATA / "tracker.json"
CACHE = DATA / "moodle_cache.json"


def _read(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, data):
    DATA.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_notes():
    notes = _read(NOTES, {})
    notes.setdefault("assessments", {})
    notes.setdefault("exams", [])
    return notes


def save_notes(notes):
    _write(NOTES, notes)


def save_cache(snapshot):
    """Keep the last good answer from Moodle, for when it can't be reached."""
    _write(CACHE, snapshot)


def load_cache():
    return _read(CACHE, None)


def add_exam(course_id, name, close_ts, weight):
    """Save an exam I've added myself (exams aren't on Moodle). With no weight given,
    use an exam weight the weight finder found in this module's files, if any."""
    with lock:
        notes = load_notes()
        found = [f for f in notes.get("scans", {}).get(str(course_id), {}).get("unmatched", [])
                 if f["kind"] == "exam"]
        source = None
        if weight is None and len({f["percent"] for f in found}) == 1:
            weight, source = found[0]["percent"], found[0]["source"]
        next_number = max([int(e["id"].split("-")[1]) for e in notes["exams"]] + [0]) + 1
        exam_id = f"exam-{next_number}"
        notes["exams"].append({
            "id": exam_id, "course_id": course_id, "name": name,
            "close": close_ts, "weight": weight, "done": False,
        })
        if source:
            notes["assessments"][exam_id] = {"weight": weight, "weight_source": source}
        save_notes(notes)


def update_assessment(assessment_id, **fields):
    """Set fields (weight, excluded, manual_done) on one assessment's notes and save."""
    with lock:
        notes = load_notes()
        notes["assessments"].setdefault(assessment_id, {}).update(fields)
        save_notes(notes)
