"""Flask web app: pages and form handlers. Run with:  python app.py"""
import json
from pathlib import Path

from flask import Flask, render_template, request

import moodle_client
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
    notes = {"assessments": {}, "exams": []}
    view = tracker.build_view(snapshot, notes, load_settings(), show_ec=show_ec)
    view["offline"] = offline
    return view


@app.route("/")
def dashboard():
    show_ec = request.args.get("ec") == "1"
    return render_template("dashboard.html", view=load_view(show_ec), show_ec=show_ec)


if __name__ == "__main__":
    app.run(debug=True)
