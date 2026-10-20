"""The "Ask Crunch" helper: answers a few questions from the data Crunch already has.
No AI model - plain rules over weights, deadlines and what's done. Free, instant, private.

Each answer is {"intro": str, "items": [{"text", "id"}], "outro": str}; "id" links an item
to its assessment page.
"""
from datetime import datetime, timedelta

QUESTIONS = [
    ("focus", "What should I focus on this week?"),
    ("important", "What's most important?"),
    ("progress", "How am I doing?"),
]


def _to_do(view):
    """Assessments that count and aren't done (EC versions excluded)."""
    return [r for m in view["modules"] for r in m["items"] if not r["ec"] and not r["completed"]]


def _label(r):
    """"IN2013 Quiz 1", without doubling the code when the name already has it ("IN2002 Exam")."""
    return r["name"] if r["name"].startswith(r["module_code"]) else f"{r['module_code']} {r['name']}"


def _weight(r):
    return f"{r['weight']:g}%" if r["weight"] is not None else "weight unknown"


def _when(r):
    if r["days_left"]:
        return r["days_left"]
    if not r["close"]:
        return f"expected {r['expected']}, date TBC" if r.get("expected") else "date TBC"
    return r["close_str"]


def focus(view, now):
    to_do = _to_do(view)
    now_ts = now.timestamp()
    week_end = (now + timedelta(days=7)).timestamp()
    overdue = [r for r in to_do if r["close"] and r["close"] < now_ts]
    this_week = sorted((r for r in to_do if r["close"] and now_ts <= r["close"] <= week_end), key=lambda r: r["close"])
    items = [{"text": f"⚠ Overdue: {_label(r)} ({_weight(r)}) — {r['countdown']}", "id": r["id"]}
             for r in overdue]
    items += [{"text": f"{_label(r)} — {_when(r)} ({_weight(r)}, {(r['priority'] or 'no').capitalize()} priority)",
               "id": r["id"]} for r in sorted(this_week, key=lambda r: -(r["weight"] or 0))]
    if items:
        intro = "Here's what needs you this week, most important first:"
    else:
        intro = "Nothing is due in the next 7 days. 🎉"
    # Something big coming up soon is worth starting early.
    month_end = (now + timedelta(days=31)).timestamp()
    big = max((r for r in to_do if r["close"] and week_end < r["close"] <= month_end and (r["weight"] or 0) > 10),
              key=lambda r: r["weight"], default=None)
    outro = (f"Start early on {_label(big)} — {_weight(big)}, {_when(big)}."
             if big else "")
    return {"intro": intro, "items": items, "outro": outro}


def important(view, now):
    ranked = sorted(_to_do(view), key=lambda r: (-(r["weight"] or 0), r["close"] or float("inf")))[:5]
    if not ranked:
        return {"intro": "Nothing left to do — everything is done. 🎉", "items": [], "outro": ""}
    return {
        "intro": "Your biggest assessments still to do, by weight:",
        "items": [{"text": f"{_label(r)} — {_weight(r)}, {_when(r)}", "id": r["id"]} for r in ranked],
        "outro": "High-weight work is where your time counts most.",
    }


def progress(view, now):
    lines, done_total, all_total = [], 0, 0
    for m in view["modules"]:
        counted = [r for r in m["items"] if not r["ec"]]
        done = sum(1 for r in counted if r["completed"])
        done_total, all_total = done_total + done, all_total + len(counted)
        if counted:
            lines.append({"text": f"{m['code']}: {done} of {len(counted)} done", "id": None})
    overdue = len(view.get("overdue", []))
    if not all_total:
        return {"intro": "No assessments found yet.", "items": [], "outro": ""}
    outro = (f"⚠ {overdue} overdue — worth sorting first." if overdue
             else "Nothing overdue — nice work." if done_total else "Nothing overdue. Good start!")
    return {"intro": f"You've done {done_total} of {all_total} assessments.", "items": lines, "outro": outro}


def answers(view, now=None):
    now = now or datetime.now()
    handlers = {"focus": focus, "important": important, "progress": progress}
    return [{"key": key, "question": question, **handlers[key](view, now)} for key, question in QUESTIONS]
