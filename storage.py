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


def _next_exam_id(notes):
    return f"exam-{max([int(e['id'].split('-')[1]) for e in notes['exams']] + [0]) + 1}"


def add_found_exam(notes, exam):
    """Add an exam the weight finder found in a module's files (caller holds the lock and saves)."""
    exam_id = _next_exam_id(notes)
    source = exam.pop("weight_source")
    notes["exams"].append({"id": exam_id, **exam})
    notes["assessments"][exam_id] = {"weight": exam["weight"], "weight_source": source}


def set_exam_date(exam_id, close_ts):
    with lock:
        notes = load_notes()
        for exam in notes["exams"]:
            if exam["id"] == exam_id:
                exam["close"] = close_ts
        save_notes(notes)


def clear_field(assessment_id, field):
    with lock:
        notes = load_notes()
        notes["assessments"].get(assessment_id, {}).pop(field, None)
        save_notes(notes)


def update_assessment(assessment_id, **fields):
    """Set fields (weight, excluded, manual_done) on one assessment's notes and save."""
    with lock:
        notes = load_notes()
        notes["assessments"].setdefault(assessment_id, {}).update(fields)
        save_notes(notes)
