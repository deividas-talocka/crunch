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


def test_no_closing_date_stays_out_of_months_but_counts_in_module():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, now=NOW)
    names = [r["name"] for month in view["months"] for r in month["rows"]]
    assert "Practice quiz" not in names
    assert view["modules"][0]["left"] == 3  # quiz 1, coursework 1, practice quiz


def test_show_ec_includes_labelled_versions():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, show_ec=True, now=NOW)
    october = view["months"][0]["rows"]
    assert [r["ec"] for r in october] == [False, True]


def test_unweighted_rows_need_weight():
    view = tracker.build_view(SNAPSHOT, {}, SETTINGS, now=NOW)
    assert all(r["priority"] is None for month in view["months"] for r in month["rows"])
