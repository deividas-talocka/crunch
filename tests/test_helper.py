import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import helper  # noqa: E402
import tracker  # noqa: E402

SETTINGS = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 10, 20, 12, 0)


def ts(*args):
    return datetime(*args).timestamp()


def item(id_, name, close, kind="quiz", open_=None):
    return {"id": id_, "course_id": 1, "name": name, "kind": kind, "open": open_ or ts(2026, 10, 1),
            "close": close, "completed": False}


SNAPSHOT = {
    "courses": [{"id": 1, "name": "IN2013 Object-Oriented Analysis and Design (PRD1 A 2026/27)"}],
    "assessments": [
        item("quiz-1", "Quiz 1", ts(2026, 10, 25, 17)),
        item("quiz-2", "Quiz 1 (Extra Time, SSP)", ts(2026, 10, 25, 17)),
        item("assign-3", "Coursework 1", ts(2026, 11, 13, 17), kind="assign"),
        item("quiz-4", "Quiz 0", ts(2026, 10, 18, 17)),
    ],
}
NOTES = {"assessments": {"quiz-1": {"weight": 2.5}, "assign-3": {"weight": 45}, "quiz-4": {"weight": 2.5}},
         "exams": [{"id": "exam-1", "course_id": 1, "name": "IN2013 Exam", "close": None, "weight": 70}]}


def answers(notes=NOTES):
    view = tracker.build_view(SNAPSHOT, notes, SETTINGS, now=NOW)
    return {a["key"]: a for a in helper.answers(view, now=NOW)}


def test_focus_lists_overdue_then_this_week_and_flags_big_work():
    focus = answers()["focus"]
    texts = [i["text"] for i in focus["items"]]
    assert texts[0].startswith("⚠ Overdue: IN2013 Quiz 0")
    assert "IN2013 Quiz 1 — 5 days left (2.5%, Low priority)" in texts[1]
    assert not any("Extra Time" in t for t in texts)
    assert "Coursework 1" in focus["outro"] and "45%" in focus["outro"]


def test_important_ranks_by_weight_including_dateless_exam():
    important = answers()["important"]
    assert [i["id"] for i in important["items"]][:2] == ["exam-1", "assign-3"]
    assert important["items"][0]["text"] == "IN2013 Exam — 70%, date TBC"  # code not repeated


def test_progress_counts_done_and_overdue():
    notes = {**NOTES, "assessments": {**NOTES["assessments"], "quiz-1": {"weight": 2.5, "manual_done": True}}}
    progress = answers(notes)["progress"]
    assert progress["intro"] == "You've done 1 of 4 assessments."
    assert progress["items"][0]["text"] == "IN2013: 1 of 4 done"
    assert "1 overdue" in progress["outro"]


def test_everything_done():
    notes = {"assessments": {k: {"manual_done": True} for k in ["quiz-1", "assign-3", "quiz-4"]}}
    a = answers(notes)
    assert a["focus"]["intro"].startswith("Nothing is due")
    assert a["important"]["intro"].startswith("Nothing left to do")
