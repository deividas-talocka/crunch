"""Talks to Moodle's web services using the personal token from .env.

Knows nothing about weights or priority - it only asks Moodle questions
and returns plain Python data.
"""
import html
import os
import re

import requests
import truststore
from dotenv import load_dotenv

# Verify HTTPS certificates with the operating system's store. requests' own
# bundled list can't verify the university's Moodle certificate chain.
truststore.inject_into_ssl()

load_dotenv()


class MoodleError(Exception):
    """Moodle could not be reached, or it refused the request."""


def _settings():
    url = os.environ.get("MOODLE_URL", "").strip().rstrip("/")
    token = os.environ.get("MOODLE_TOKEN", "").strip()
    if not url or not token:
        raise MoodleError("MOODLE_URL and MOODLE_TOKEN must be set in .env")
    return url, token


def _flatten(params):
    """Turn {"courseids": [1, 2]} into {"courseids[0]": 1, "courseids[1]": 2},
    which is the form Moodle's REST interface expects for lists."""
    flat = {}
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                flat[f"{key}[{i}]"] = item
        else:
            flat[key] = value
    return flat


def call(function, **params):
    """Ask Moodle one question (a web service function) and return its JSON reply."""
    url, token = _settings()
    query = {
        "wstoken": token,               # who I am
        "wsfunction": function,         # what I'm asking
        "moodlewsrestformat": "json",   # answer as JSON
        **_flatten(params),
    }
    try:
        response = requests.get(f"{url}/webservice/rest/server.php", params=query, timeout=20)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        # Don't include the request URL in the message: it contains the token.
        raise MoodleError(f"Could not reach Moodle ({type(exc).__name__})") from None
    if isinstance(data, dict) and "exception" in data:
        raise MoodleError(f"{function}: {data.get('errorcode')} - {data.get('message')}")
    return data


def site_info():
    return call("core_webservice_get_site_info")


def current_courses():
    """This year's modules: the ones Moodle classifies as in progress."""
    return call(
        "core_course_get_enrolled_courses_by_timeline_classification",
        classification="inprogress",
    )["courses"]


def quizzes(course_ids):
    return call("mod_quiz_get_quizzes_by_courses", courseids=course_ids)["quizzes"]


def assignments(course_ids):
    result = []
    for course in call("mod_assign_get_assignments", courseids=course_ids)["courses"]:
        for assignment in course["assignments"]:
            result.append({**assignment, "course": course["id"]})
    return result


def _clean(text):
    """Moodle sends names HTML-escaped ("&amp;") and sometimes with double spaces."""
    return " ".join(html.unescape(text or "").split())


def _plain(intro):
    """An activity's description as plain text (it arrives as HTML)."""
    return _clean(re.sub(r"<[^>]+>", " ", intro or ""))


def fetch_snapshot():
    """Everything the app needs from Moodle, as plain data:
    {"courses": [{id, name}], "assessments": [{id, course_id, name, kind, open, close, completed}]}
    Times are Unix timestamps, or None when Moodle has no date set.
    """
    courses = [{"id": c["id"], "name": _clean(c["fullname"])} for c in current_courses()]
    ids = [c["id"] for c in courses]
    found = []
    if ids:
        for q in quizzes(ids):
            found.append({
                "id": f"quiz-{q['id']}", "moodle_id": q["id"], "course_id": q["course"],
                "name": _clean(q["name"]), "kind": "quiz", "description": _plain(q.get("intro")),
                "open": q.get("timeopen") or None, "close": q.get("timeclose") or None,
                "completed": False,
            })
        for a in assignments(ids):
            found.append({
                "id": f"assign-{a['id']}", "moodle_id": a["id"], "course_id": a["course"],
                "name": _clean(a["name"]), "kind": "assign", "description": _plain(a.get("intro")),
                "open": a.get("allowsubmissionsfromdate") or None, "close": a.get("duedate") or None,
                "completed": False,
            })
    return {"courses": courses, "assessments": found}
