"""Reads and writes my notes (data/tracker.json). The data folder is gitignored."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
NOTES = DATA / "tracker.json"


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


def update_assessment(assessment_id, **fields):
    """Set fields (weight, excluded, manual_done) on one assessment's notes and save."""
    notes = load_notes()
    notes["assessments"].setdefault(assessment_id, {}).update(fields)
    save_notes(notes)
