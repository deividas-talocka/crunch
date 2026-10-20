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
         "open": ts(2026, 10, 1), "close": ts(2099, 10, 25, 17), "completed": False,
         "description": "Lecture 1 and 2 covers queues.", "url": "https://moodle.example/mod/quiz/view.php?id=1"},
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


@pytest.mark.parametrize("path", ["/", "/?ec=1", "/?m=1", "/module/1", "/module/1?ec=1", "/completed",
                                  "/assessment/quiz-1", "/assessment/quiz-2", "/assessment/assign-3",
                                  "/assessment/exam-1"])
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "Crunch" in response.get_data(as_text=True)


def test_assessment_page_shows_details_and_moodle_link(client):
    html = client.get("/assessment/quiz-1").get_data(as_text=True)
    assert "2.5%" in html and "from intro.pdf" in html and "Open in Moodle" in html
    assert "Lecture 1 and 2 covers queues" in html  # Moodle's description
    exam = client.get("/assessment/exam-1").get_data(as_text=True)
    assert "Set date" in exam and "exam in January" in exam and "Open in Moodle" not in exam
    assert client.get("/assessment/nope").status_code == 404


def test_module_page_links_to_moodle_course(client, monkeypatch):
    monkeypatch.setattr(moodle_client, "_settings", lambda: ("https://moodle.example", "token"))
    html = client.get("/module/1").get_data(as_text=True)
    assert 'href="https://moodle.example/course/view.php?id=1"' in html and "Open module in Moodle" in html


def test_setting_a_date_moves_it_into_the_months(client, monkeypatch):
    monkeypatch.setattr(app_module, "MONTHS_SHOWN", 12)
    before = client.get("/").get_data(as_text=True)
    assert "IN2013 Exam" in before.split("Coming up — date to confirm")[1]
    client.post("/exam/exam-1/date", data={"close": "2099-03-14T09:30"})
    after = client.get("/").get_data(as_text=True)
    assert "Coming up — date to confirm" not in after
    march = after.split("March 2099")[1]
    assert "IN2013 Exam" in march and "Sat 14 Mar" in march


def test_overdue_section(client):
    storage.update_assessment("assign-3", manual_done=False)
    SNAPSHOT["assessments"][2]["completed"] = False
    try:
        html = client.get("/").get_data(as_text=True)
        assert "Overdue · 1" in html and html.index("Overdue") < html.index("Upcoming by month")
    finally:
        SNAPSHOT["assessments"][2]["completed"] = True


def test_first_and_last_buttons(client, monkeypatch):
    monkeypatch.setattr(app_module, "MONTHS_SHOWN", 1)  # sample data has two months; page one at a time
    first = client.get("/").get_data(as_text=True)
    assert 'disabled">⏮ First' in first and "Last ⏭</a>" in first
    last_href = first.split("Last ⏭</a>")[0].rsplit('href="', 1)[1].split('"')[0]
    last = client.get("/" + last_href).get_data(as_text=True)
    assert 'disabled">Last ⏭' in last and "⏮ First</a>" in last


def test_finished_months_disappear_and_all_done_shows_nothing_coming_up(client):
    storage.update_assessment("quiz-1", manual_done=True)  # the only October 2099 assessment
    html = client.get("/?m=99").get_data(as_text=True)
    assert "October 2099" not in html and "January" in html  # the exam expected in January stays
    storage.update_assessment("exam-1", manual_done=True)
    html = client.get("/").get_data(as_text=True)
    assert "Nothing coming up" in html
    assert "Every module is done" in html and 'class="module-card"' not in html
    assert client.get("/module/1").status_code == 200  # its page is still there


def test_date_to_confirm_section_is_below_the_months(client):
    html = client.get("/").get_data(as_text=True)
    assert html.index("Upcoming by month") < html.index("Coming up — date to confirm")
    assert "Expected January" in html
