"""Talks to Moodle's web services using the personal token from .env.

Knows nothing about weights or priority - it only asks Moodle questions
and returns plain Python data.
"""
import html
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

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


def grades(course_id, user_id):
    """My released grades in one course, as {("quiz", 123): 80.0, ("assign", 45): 65.5} (percent)."""
    found = {}
    report = call("gradereport_user_get_grade_items", courseid=course_id, userid=user_id)
    for grade_item in report["usergrades"][0]["gradeitems"]:
        raw, top = grade_item.get("graderaw"), grade_item.get("grademax")
        if grade_item.get("itemtype") == "mod" and raw is not None and top:
            found[(grade_item.get("itemmodule"), grade_item.get("iteminstance"))] = round(raw / top * 100, 1)
    return found


def _course_grades(course_id, user_id):
    try:
        return grades(course_id, user_id)
    except MoodleError:
        return {}  # grades not shared for this course: Crunch works without them


def quiz_finished(quiz_id):
    return bool(call("mod_quiz_get_user_attempts", quizid=quiz_id, status="finished").get("attempts"))


def assignment_submitted(assign_id):
    attempt = call("mod_assign_get_submission_status", assignid=assign_id).get("lastattempt") or {}
    submission = attempt.get("submission") or attempt.get("teamsubmission") or {}
    return submission.get("status") == "submitted"


def _completed(item):
    """Ask Moodle whether I've done this one. If Moodle won't say, treat it as not done
    (the manual tick still works)."""
    try:
        if item["kind"] == "quiz":
            return quiz_finished(item["moodle_id"])
        return assignment_submitted(item["moodle_id"])
    except MoodleError:
        return False


def fetch_snapshot(module_pattern=None):
    """Everything the app needs from Moodle, as plain data:
    {"courses": [{id, name}], "assessments": [{id, course_id, name, kind, open, close, completed}]}
    Times are Unix timestamps, or None when Moodle has no date set.
    module_pattern (a regex) limits it to courses whose name looks like a module.
    """
    courses = [{"id": c["id"], "name": _clean(c["fullname"])} for c in current_courses()]
    if module_pattern:
        courses = [c for c in courses if re.match(module_pattern, c["name"])]
    ids = [c["id"] for c in courses]
    base_url = _settings()[0]
    found = []
    if ids:
        for q in quizzes(ids):
            found.append({
                "id": f"quiz-{q['id']}", "moodle_id": q["id"], "course_id": q["course"],
                "name": _clean(q["name"]), "kind": "quiz", "description": _plain(q.get("intro")),
                "url": f"{base_url}/mod/quiz/view.php?id={q['coursemodule']}" if q.get("coursemodule") else None,
                "open": q.get("timeopen") or None, "close": q.get("timeclose") or None,
                "completed": False,
            })
        for a in assignments(ids):
            found.append({
                "id": f"assign-{a['id']}", "moodle_id": a["id"], "course_id": a["course"],
                "name": _clean(a["name"]), "kind": "assign", "description": _plain(a.get("intro")),
                "url": f"{base_url}/mod/assign/view.php?id={a['cmid']}" if a.get("cmid") else None,
                "open": a.get("allowsubmissionsfromdate") or None, "close": a.get("duedate") or None,
                "completed": False,
            })

    # Completion: one call per assessment, so only ask about ones that have opened,
    # and ask several at once.
    now = time.time()
    started = [item for item in found if not item["open"] or item["open"] <= now]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for item, done in zip(started, pool.map(_completed, started)):
            item["completed"] = done
        # Released grades, one call per module.
        if ids:
            user_id = site_info()["userid"]
            course_grades = {}
            for course_id, result in zip(ids, pool.map(lambda c: _course_grades(c, user_id), ids)):
                course_grades.update(result)
            for item in found:
                item["grade"] = course_grades.get((item["kind"], item["moodle_id"]))
    return {"courses": courses, "assessments": found}
