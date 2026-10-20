"""Flask web app: pages and form handlers. Run with:  python app.py"""
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request

import moodle_client
import storage
import tracker
from moodle_client import MoodleError

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)


def load_settings():
    return json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))


def load_view(show_ec=False):
    """Ask Moodle, merge in my notes, and build what the pages show."""
    offline = False
    try:
        snapshot = moodle_client.fetch_snapshot()
    except MoodleError:
        snapshot, offline = {"courses": [], "assessments": []}, True
    view = tracker.build_view(snapshot, storage.load_notes(), load_settings(), show_ec=show_ec)
    view["offline"] = offline
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
    return render_template("module.html", view=view, module=found, show_ec=show_ec)


@app.post("/module/<int:course_id>/exam")
def add_exam(course_id):
    name = request.form.get("name", "").strip()
    when = request.form.get("close", "")
    try:
        close_ts = datetime.strptime(when, "%Y-%m-%dT%H:%M").timestamp()
    except ValueError:
        return back()  # name and date are required; the form enforces them too
    weight = parse_weight(request.form.get("weight", ""))
    if name:
        storage.add_exam(course_id, name, close_ts, weight)
    return back()


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
    storage.update_assessment(assessment_id, weight=parse_weight(request.form.get("weight", "")))
    return back()


@app.post("/assessment/<assessment_id>/exclude")
def exclude(assessment_id):
    storage.update_assessment(assessment_id, excluded=True, included=False)
    return back()


@app.post("/assessment/<assessment_id>/include")
def include(assessment_id):
    """Undo "Doesn't count", or overrule the automatic optional check."""
    storage.update_assessment(assessment_id, excluded=False, included=True)
    return back()


if __name__ == "__main__":
    app.run(debug=True)
