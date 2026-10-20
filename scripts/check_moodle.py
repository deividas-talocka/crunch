"""Step-1 connection check: can we talk to Moodle, and does it answer the way the spec assumes?

Run from the project folder:  python scripts/check_moodle.py
"""
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import moodle_client  # noqa: E402
from moodle_client import MoodleError  # noqa: E402


def when(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%a %d %b %Y %H:%M") if timestamp else "-"


def main():
    info = moodle_client.site_info()
    print(f"Connected to: {info['sitename']}\n")

    courses = moodle_client.current_courses()
    print(f"In-progress modules ({len(courses)}):")
    for course in courses:
        print(f"  [{course['id']}] {course['fullname']}")
    if not courses:
        return
    names = {c["id"]: c["shortname"] for c in courses}
    ids = list(names)

    print("\nQuizzes:")
    for q in moodle_client.quizzes(ids):
        print(f"  {names.get(q['course'], q['course'])}: {q['name']}  open {when(q['timeopen'])}  close {when(q['timeclose'])}")

    print("\nAssignments (coursework):")
    for a in moodle_client.assignments(ids):
        print(f"  {names.get(a['course'], a['course'])}: {a['name']}  from {when(a['allowsubmissionsfromdate'])}  due {when(a['duedate'])}")

    # Activity types that show up on the Moodle timeline - anything other than
    # quiz/assign (e.g. Turnitin) would be missed by the two calls above.
    print("\nActivity types on your Moodle timeline (next 365 days):")
    try:
        now = int(datetime.now().timestamp())
        events = moodle_client.call(
            "core_calendar_get_action_events_by_timesort",
            timesortfrom=now - 60 * 86400, timesortto=now + 365 * 86400, limitnum=50,
        )["events"]
        for kind, count in Counter(e.get("modulename") or "other" for e in events).most_common():
            print(f"  {kind}: {count}")
    except MoodleError as exc:
        print(f"  (timeline not available: {exc})")


if __name__ == "__main__":
    try:
        main()
    except MoodleError as exc:
        print(f"Moodle check failed: {exc}")
        sys.exit(1)
