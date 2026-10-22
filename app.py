"""Flask web app: pages and form handlers. Run with:  python app.py"""
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request

import helper
import moodle_client
import storage
import tracker
import weight_finder
from moodle_client import MoodleError

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)


def load_settings():
    return json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))


def load_view(show_ec=False):
    """Ask Moodle, merge in my notes, and build what the pages show."""
    settings = load_settings()
    offline = False
    try:
        snapshot = moodle_client.fetch_snapshot(settings["module_code_pattern"])
        snapshot["fetched_at"] = datetime.now().timestamp()
        storage.save_cache(snapshot)
    except MoodleError:
        # Offline: show the last assessments we loaded, with the offline banner.
        snapshot = storage.load_cache() or {"courses": [], "assessments": []}
        offline = True
    notes = storage.load_notes()
    view = tracker.build_view(snapshot, notes, settings, show_ec=show_ec)
    view["offline"] = offline
    if not offline:
        # Weights are found by themselves, in the background, when a module needs it.
        all_rows = tracker.build_view(snapshot, notes, settings, show_ec=True)["modules"]
        weight_finder.start(weight_finder.courses_needing_scan(all_rows, notes))
    view["finding_weights"] = weight_finder.is_running()
    view["helper"] = helper.answers(view)
    fetched = snapshot.get("fetched_at")
    view["updated"] = datetime.fromtimestamp(fetched).strftime("%a %d %b, %H:%M") if fetched else None
    view["github_url"] = settings.get("github_url") or None
    view["linkedin_url"] = settings.get("linkedin_url") or None
    view["year_of_study"] = settings.get("year_of_study")
    view["scans"] = notes.get("scans", {})
    return view


def back(default="/"):
    """Return to the page the form was submitted from."""
    return redirect(request.referrer or default)


MONTHS_SHOWN = 2  # month columns visible at once; the arrow buttons move through the rest


@app.route("/")
def dashboard():
    show_ec = request.args.get("ec") == "1"
    view = load_view(show_ec)
    last_start = max(len(view["months"]) - MONTHS_SHOWN, 0)
    start = min(max(request.args.get("m", 0, type=int), 0), last_start)
    return render_template(
        "dashboard.html", view=view, show_ec=show_ec,
        months=view["months"][start:start + MONTHS_SHOWN],
        prev_m=start - 1 if start > 0 else None,
        next_m=start + 1 if start < last_start else None,
        first_m=0 if start > 0 else None,
        last_m=last_start if start < last_start else None,
    )


@app.route("/module/<int:course_id>")
def module(course_id):
    show_ec = request.args.get("ec") == "1"
    view = load_view(show_ec=True)
    found = next((m for m in view["modules"] if m["id"] == course_id), None)
    if found is None:
        abort(404)
    if not show_ec:
        found["items"] = [r for r in found["items"] if not r["ec"]]
        found["optional"] = [r for r in found["optional"] if not r["ec"]]
    try:
        moodle_url = f"{moodle_client._settings()[0]}/course/view.php?id={course_id}"
    except MoodleError:
        moodle_url = None
    return render_template("module.html", view=view, module=found, show_ec=show_ec, moodle_url=moodle_url)


def parse_weight(raw):
    """"30", "2.5" or "30%" -> a number between 0 and 100; anything else -> None."""
    raw = raw.strip().rstrip("%")
    try:
        weight = float(raw) if raw else None
    except ValueError:
        return None
    if weight is None or not 0 < weight <= 100:
        return None
    return int(weight) if weight.is_integer() else weight


@app.post("/assessment/<assessment_id>/weight")
def set_weight(assessment_id):
    # A weight I type replaces a found one and is never overwritten by the finder.
    storage.update_assessment(assessment_id, weight=parse_weight(request.form.get("weight", "")), weight_source=None)
    return back()


@app.post("/assessment/<assessment_id>/grade")
def set_grade(assessment_id):
    """Type in my mark (percent) for something Moodle doesn't grade, like an exam. Empty clears it."""
    mark = parse_weight(request.form.get("grade", ""))
    if mark is None:
        storage.clear_field(assessment_id, "manual_grade")
    else:
        storage.update_assessment(assessment_id, manual_grade=mark)
    return back()


@app.post("/assessment/<assessment_id>/exclude")
def exclude(assessment_id):
    storage.update_assessment(assessment_id, excluded=True, included=False)
    return back()


@app.route("/assessment/<assessment_id>")
def assessment(assessment_id):
    view = load_view(show_ec=True)
    for m in view["modules"]:
        for r in m["items"] + m["optional"]:
            if r["id"] == assessment_id:
                return render_template("assessment.html", view=view, r=r, module=m)
    abort(404)


@app.post("/exam/<exam_id>/date")
def set_exam_date(exam_id):
    try:
        close_ts = datetime.strptime(request.form.get("close", ""), "%Y-%m-%dT%H:%M").timestamp()
    except ValueError:
        return back()
    storage.set_exam_date(exam_id, close_ts)
    return back()


@app.route("/completed")
def completed():
    return render_template("completed.html", view=load_view(show_ec=True))


@app.post("/assessment/<assessment_id>/tick")
def tick(assessment_id):
    """Manual done / not done, for exams and anything Moodle can't report."""
    storage.update_assessment(assessment_id, manual_done=request.form.get("done") == "1")
    return back()


@app.post("/assessment/<assessment_id>/include")
def include(assessment_id):
    """Undo "Doesn't count", or overrule the automatic optional check."""
    storage.update_assessment(assessment_id, excluded=False, included=True)
    return back()


if __name__ == "__main__":
    app.run(debug=True)
