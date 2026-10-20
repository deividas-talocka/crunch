import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tracker  # noqa: E402

SETTINGS = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 10, 20, 12, 0)


def ts(*args):
    return datetime(*args).timestamp()


def item(id_, course_id, name, close, kind="quiz", open_=None):
    return {"id": id_, "course_id": course_id, "name": name, "kind": kind,
            "open": open_, "close": close, "completed": False}


SNAPSHOT = {
    "courses": [
        {"id": 1, "name": "IN2013 Object-Oriented Analysis and Design (PRD1 A 2026/27)"},
        {"id": 2, "name": "Library Induction (2026/27)"},
    ],
    "assessments": [
        item("quiz-1", 1, "Quiz 1 on Lecture 1 and 2", ts(2026, 10, 25, 17)),
        item("quiz-2", 1, "Quiz 1 on Lecture 1 and 2 (Extra Time, SSP)", ts(2026, 10, 25, 17)),
        item("assign-3", 1, "Coursework 1 (Analysis) Submission Area", ts(2026, 11, 13, 17), kind="assign"),
        item("quiz-4", 2, "Library quiz", ts(2026, 10, 30, 17)),
        item("quiz-5", 1, "Practice quiz", None),
    ],
}


def test_is_ec_matches_real_moodle_names():
    kw = SETTINGS["ec_keywords"]
    assert tracker.is_ec("Quiz 1 on Lecture 1 and 2 (Extra Time,SSP)", kw)
    assert tracker.is_ec("Quiz 3 on Lecture 5 and 6 (Extra time)", kw)
    assert tracker.is_ec("Quiz 1 on Lecture 1 and 2 (Extenuating Circumstances and extensions)", kw)
    assert tracker.is_ec("CW1 (Analysis) submission area (2026-27) - Extenuating Circumstances and extensions", kw)
    assert not tracker.is_ec("Quiz 1 on Lecture 1 and 2", kw)
    assert not tracker.is_ec("Coursework 1 (Analysis) Submission Area (2026 - 27)", kw)


def test_assessment_type():
    tk = SETTINGS["type_keywords"]
    assert tracker.assessment_type("Quiz 2", "quiz", tk) == "Quiz"
    assert tracker.assessment_type("Assessment 1 submission area", "assign", tk) == "Coursework"
    assert tracker.assessment_type("DSA Viva", "assign", tk) == "Viva"


def test_only_current_modules_and_no_ec_by_default():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, now=NOW)
    assert [m["code"] for m in view["modules"]] == ["IN2013"]
    names = [r["name"] for month in view["months"] for r in month["rows"]]
    assert "Library quiz" not in names
    assert not any("Extra Time" in n for n in names)


def test_grouped_by_closing_month_from_current_month():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, now=NOW)
    labels = [m["label"] for m in view["months"]]
    assert labels == ["October 2026", "November 2026"]
    october, november = view["months"]
    assert [r["name"] for r in october["rows"]] == ["Quiz 1 on Lecture 1 and 2"]
    assert [r["name"] for r in november["rows"]] == ["Coursework 1 (Analysis) Submission Area"]


def test_no_closing_date_is_optional():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, now=NOW)
    names = [r["name"] for month in view["months"] for r in month["rows"]]
    assert "Practice quiz" not in names
    module = view["modules"][0]
    assert module["left"] == 2  # quiz 1, coursework 1
    assert [(r["name"], r["optional_reason"]) for r in module["optional"]] == [("Practice quiz", "No closing date")]


def test_formative_detected_from_name_or_description():
    s = SETTINGS
    base = {"kind": "assign", "close": ts(2026, 11, 8, 17)}
    assert tracker.optional_reason({**base, "name": "Formative Activity – SHA-256 Hash Challenge"}, s)
    assert tracker.optional_reason({**base, "name": "Hash challenge",
                                    "description": "It is just a fun! ... there is no mark for this activity."}, s)
    assert tracker.optional_reason({**base, "name": "Coursework 1 (Analysis) Submission Area",
                                    "description": "Please consult the Programme Handbook."}, s) is None
    assert tracker.optional_reason({"kind": "exam", "close": None, "name": "DSA Exam"}, s) is None


def test_counts_button_overrides_optional_and_doesnt_count_is_undoable():
    notes = {"assessments": {"quiz-5": {"included": True}, "assign-3": {"excluded": True}}}
    view = tracker.build_view(SNAPSHOT, notes, SETTINGS, now=NOW)
    module = view["modules"][0]
    assert "quiz-5" in [r["id"] for r in module["items"]]
    assert [(r["id"], r["optional_reason"]) for r in module["optional"]] == [("assign-3", "Marked by you")]


def test_show_ec_includes_labelled_versions():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, show_ec=True, now=NOW)
    october = view["months"][0]["rows"]
    assert [r["ec"] for r in october] == [False, True]


def test_priority_thresholds():
    assert tracker.priority(2.5) == "low"
    assert tracker.priority(10) == "low"
    assert tracker.priority(30) == "medium"
    assert tracker.priority(50) == "medium"
    assert tracker.priority(70) == "high"
    assert tracker.priority(None) is None


def test_weights_and_exclusions_from_notes():
    notes = {"assessments": {"quiz-1": {"weight": 2.5}, "assign-3": {"weight": 70}, "quiz-5": {"excluded": True}}}
    view = tracker.build_view(SNAPSHOT, notes, SETTINGS, now=NOW)
    rows = {r["id"]: r for month in view["months"] for r in month["rows"]}
    assert rows["quiz-1"]["priority"] == "low"
    assert rows["assign-3"]["priority"] == "high"
    assert view["modules"][0]["left"] == 2  # practice quiz no longer counted


def test_open_status():
    now = ts(2026, 10, 20, 12)
    assert tracker.open_status(ts(2026, 10, 19, 17), ts(2026, 10, 25, 17), now) == "open"
    assert tracker.open_status(ts(2026, 11, 2, 17), ts(2026, 11, 8, 17), now) == "not_open"
    assert tracker.open_status(None, ts(2026, 11, 19, 9), now) == "not_open"  # no opening date: not out yet
    assert tracker.open_status(ts(2026, 10, 1), ts(2026, 10, 5), now) == "closed"


def test_added_exam_lands_in_its_month_with_priority():
    notes = {"exams": [{"id": "exam-1", "course_id": 1, "name": "OOAD Exam",
                        "close": ts(2027, 1, 14, 9, 30), "weight": 70, "done": False}]}
    view = tracker.build_view(SNAPSHOT, notes, SETTINGS, now=NOW)
    january = next(m for m in view["months"] if m["label"] == "January 2027")
    exam = january["rows"][0]
    assert (exam["name"], exam["type"], exam["priority"], exam["ec"]) == ("OOAD Exam", "Exam", "high", False)
    assert view["modules"][0]["left"] == 3


def test_completed_moves_out_of_months_and_counts():
    snapshot = {**SNAPSHOT, "assessments": [dict(a) for a in SNAPSHOT["assessments"]]}
    snapshot["assessments"][0]["completed"] = True  # Moodle says quiz-1 is done
    notes = {"assessments": {"assign-3": {"manual_done": True}}}  # I ticked coursework 1
    view = tracker.build_view(snapshot, notes, SETTINGS, now=NOW)
    in_months = [r["id"] for month in view["months"] for r in month["rows"]]
    assert "quiz-1" not in in_months and "assign-3" not in in_months
    assert {r["id"]: r["moodle_completed"] for r in view["completed"]} == {"quiz-1": True, "assign-3": False}
    assert view["modules"][0]["left"] == 0


def test_exam_without_date_goes_in_named_month_or_tbc_list():
    notes = {"exams": [
        {"id": "exam-1", "course_id": 1, "name": "IN2013 Exam", "close": None, "month": 1, "weight": 70, "auto": True},
        {"id": "exam-2", "course_id": 1, "name": "Other Exam", "close": None, "month": None, "weight": 50},
    ]}
    view = tracker.build_view(SNAPSHOT, notes, SETTINGS, now=NOW)
    january = next(m for m in view["months"] if m["label"] == "January 2027")
    assert [(r["name"], r["close_str"]) for r in january["rows"]] == [("IN2013 Exam", "Date TBC")]
    assert [r["name"] for r in view["exams_tbc"]] == ["Other Exam"]
    assert view["stats"]["next"]["name"] == "Quiz 1 on Lecture 1 and 2"


def test_unweighted_rows_need_weight():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, now=NOW)
    assert all(r["priority"] is None for month in view["months"] for r in month["rows"])
