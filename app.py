"""Flask web app: pages and form handlers. Run with:  python app.py"""
import json
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


@app.route("/")
def dashboard():
    show_ec = request.args.get("ec") == "1"
    return render_template("dashboard.html", view=load_view(show_ec), show_ec=show_ec)


@app.route("/module/<int:course_id>")
def module(course_id):
    view = load_view(show_ec=True)
    found = next((m for m in view["modules"] if m["id"] == course_id), None)
    if found is None:
        abort(404)
    return render_template("module.html", view=view, module=found)


@app.post("/assessment/<assessment_id>/weight")
def set_weight(assessment_id):
    raw = request.form.get("weight", "").strip().rstrip("%")
    try:
        weight = float(raw) if raw else None
    except ValueError:
        weight = None
    if weight is not None and not 0 < weight <= 100:
        weight = None
    if weight is not None and weight.is_integer():
        weight = int(weight)
    storage.update_assessment(assessment_id, weight=weight)
    return back()


@app.post("/assessment/<assessment_id>/exclude")
def exclude(assessment_id):
    storage.update_assessment(assessment_id, excluded=True)
    return back()


if __name__ == "__main__":
    app.run(debug=True)
