"""Renders every page with sample data, so a broken template fails the tests.
No Moodle calls: the snapshot is faked and notes go to a temporary folder."""
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as app_module  # noqa: E402
import moodle_client  # noqa: E402
import storage  # noqa: E402
import weight_finder  # noqa: E402


def ts(*args):
    return datetime(*args).timestamp()


SNAPSHOT = {
    "courses": [{"id": 1, "name": "IN2013 Object-Oriented Analysis and Design (PRD1 A 2026/27)"}],
    "assessments": [
        {"id": "quiz-1", "moodle_id": 1, "course_id": 1, "name": "Quiz 1 on Lecture 1 and 2", "kind": "quiz",
         "open": ts(2026, 10, 1), "close": ts(2099, 10, 25, 17), "completed": False},
        {"id": "quiz-2", "moodle_id": 2, "course_id": 1, "name": "Quiz 1 on Lecture 1 and 2 (Extra Time, SSP)",
         "kind": "quiz", "open": ts(2026, 10, 1), "close": ts(2099, 10, 25, 17), "completed": False},
        {"id": "assign-3", "moodle_id": 3, "course_id": 1, "name": "Coursework 1", "kind": "assign",
         "open": None, "close": ts(2026, 1, 1), "completed": True},
    ],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA", tmp_path)
    monkeypatch.setattr(storage, "NOTES", tmp_path / "tracker.json")
    monkeypatch.setattr(storage, "CACHE", tmp_path / "cache.json")
    monkeypatch.setattr(moodle_client, "fetch_snapshot", lambda pattern=None: SNAPSHOT)
    monkeypatch.setattr(weight_finder, "start", lambda modules: None)
    storage.save_notes({"assessments": {"quiz-1": {"weight": 2.5, "weight_source": "intro.pdf"}},
                        "exams": [{"id": "exam-1", "course_id": 1, "name": "IN2013 Exam", "close": None,
                                   "month": 1, "weight": 70, "auto": True, "hint": "exam in January"}]})
    return app_module.app.test_client()


@pytest.mark.parametrize("path", ["/", "/?ec=1", "/?m=1", "/module/1", "/module/1?ec=1", "/completed"])
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "Crunch" in response.get_data(as_text=True)


def test_finished_months_disappear_and_all_done_shows_nothing_coming_up(client):
    storage.update_assessment("quiz-1", manual_done=True)  # the only October 2099 assessment
    html = client.get("/?m=99").get_data(as_text=True)
    assert "October 2099" not in html and "January" in html  # the exam expected in January stays
    storage.update_assessment("exam-1", manual_done=True)
    assert "Nothing coming up" in client.get("/").get_data(as_text=True)


def test_date_to_confirm_section_is_below_the_months(client):
    html = client.get("/").get_data(as_text=True)
    assert html.index("Upcoming by month") < html.index("Coming up — date to confirm")
    assert "Expected January" in html
