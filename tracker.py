"""Pure logic: turns a Moodle snapshot plus my notes into what the pages show.

No web calls and no file access here, so everything can be tested directly.
"""
import re
from datetime import datetime


def priority(weight):
    """<=10% low, over 10% up to 50% medium, over 50% high; no weight -> None."""
    if weight is None:
        return None
    if weight <= 10:
        return "low"
    if weight <= 50:
        return "medium"
    return "high"


def is_ec(name, keywords):
    """True if the name mentions any EC / extra-time keyword as whole words."""
    lowered = name.lower()
    return any(re.search(rf"\b{re.escape(k.lower())}\b", lowered) for k in keywords)


def optional_reason(item, settings):
    """Why an assessment looks optional (doesn't count towards the module), or None.

    No closing date, "formative"/"practice"/"optional" in the name, or a description
    saying something like "no mark". Exams I add myself are never optional.
    """
    if item["kind"] == "exam":
        return None
    if not item["close"]:
        if item["kind"] == "quiz":
            return "Optional practice quiz — no closing date, so it isn't assessed"
        return "No closing date"
    name = item["name"].lower()
    for keyword in settings["optional_name_keywords"]:
        if re.search(rf"\b{re.escape(keyword)}\b", name):
            return f'Name says "{keyword}"'
    description = item.get("description", "").lower()
    for phrase in settings["optional_description_phrases"]:
        if re.search(rf"\b{re.escape(phrase)}\b", description):
            return f'Description says "{phrase}"'
    return None


def open_status(open_ts, close_ts, now_ts):
    """"open" (ready to do now), "not_open" (opens later, or no opening date yet), or "closed"."""
    if close_ts and close_ts < now_ts:
        return "closed"
    if not open_ts or open_ts > now_ts:
        return "not_open"  # no opening date means it isn't out yet
    return "open"


def assessment_type(name, kind, type_keywords):
    lowered = name.lower()
    for keyword, label in type_keywords.items():
        if re.search(rf"\b{re.escape(keyword.lower())}\b", lowered):
            return label
    return {"quiz": "Quiz", "assign": "Coursework", "exam": "Exam"}.get(kind, "Assessment")


def module_code(course_name, pattern):
    match = re.match(pattern, course_name)
    return match.group(0) if match else None


def module_title(course_name):
    """"IN2002 Data Structures and Algorithms (PRD1 A 2026/27)" -> without the bracketed term."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", course_name)


def _month_key(timestamp):
    d = datetime.fromtimestamp(timestamp)
    return (d.year, d.month)


def _hint_key(month, now):
    """A month named in a module file ("exam in January") -> its next (year, month)."""
    if not month:
        return None
    return (now.year, month) if month >= now.month else (now.year + 1, month)


def countdown(close_ts, now_ts):
    """"closes in 5 days", "closes today", "closed 2 days ago"..."""
    if not close_ts:
        return None
    days = (datetime.fromtimestamp(close_ts).date() - datetime.fromtimestamp(now_ts).date()).days
    if close_ts < now_ts:
        return "closed today" if days == 0 else f"closed {-days} day{'s' if days != -1 else ''} ago"
    if days == 0:
        return "closes today"
    if days == 1:
        return "closes tomorrow"
    return f"closes in {days} days"


def days_left(close_ts, now_ts):
    """Short countdown for tables: ("5 days left", "soon"), ("Tomorrow", "urgent")...
    The second value is how urgent it is: "urgent" (2 days or less), "soon" (a week), or "later"."""
    if not close_ts or close_ts < now_ts:
        return None, None
    days = (datetime.fromtimestamp(close_ts).date() - datetime.fromtimestamp(now_ts).date()).days
    label = "Today" if days == 0 else "Tomorrow" if days == 1 else f"{days} days left"
    return label, "urgent" if days <= 2 else "soon" if days <= 7 else "later"


def _fmt_full(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%A %d %B %Y, %H:%M") if timestamp else None


def _next_month(key):
    year, month = key
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _fmt_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%a %d %b") if timestamp else "—"


def _fmt_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "—"


def build_view(snapshot, notes, settings, show_ec=False, now=None):
    """Everything the dashboard, module and completed pages need.

    snapshot: from moodle_client.fetch_snapshot()
    notes:    my tracker.json contents ({"assessments": {...}, "exams": [...]})
    """
    now = now or datetime.now()
    now_ts = now.timestamp()
    pattern = settings["module_code_pattern"]
    my_notes = notes.get("assessments", {})

    modules = {}
    for course in snapshot["courses"]:
        code = module_code(course["name"], pattern)
        if code:
            modules[course["id"]] = {
                "id": course["id"], "code": code, "title": module_title(course["name"]),
                "left": 0, "items": [], "optional": [],
            }

    items = list(snapshot["assessments"])
    for exam in notes.get("exams", []):
        items.append({
            "id": exam["id"], "course_id": exam["course_id"], "name": exam["name"], "kind": "exam",
            "open": None, "close": exam["close"], "completed": False, "manual_exam": True,
            "weight": exam.get("weight"), "manual_done": exam.get("done", False),
            "month": exam.get("month"), "auto": exam.get("auto", False), "hint": exam.get("hint"),
        })

    rows = []
    for item in items:
        module = modules.get(item["course_id"])
        if module is None:
            continue  # not a current module (e.g. Library Induction)
        note = my_notes.get(item["id"], {})
        if note.get("excluded"):
            reason = "Marked by you"
        elif note.get("included"):
            reason = None  # I said it counts, whatever the automatic check thinks
        else:
            reason = optional_reason(item, settings)
        weight = note.get("weight", item.get("weight"))  # an exam's weight can be edited later
        done = item["completed"] or item.get("manual_done") or note.get("manual_done", False)
        row = {
            "id": item["id"], "module_id": module["id"], "module_code": module["code"],
            "name": item["name"], "kind": item["kind"],
            "type": assessment_type(item["name"], item["kind"], settings["type_keywords"]),
            "weight": weight, "priority": priority(weight), "weight_source": note.get("weight_source"),
            "ec": item["kind"] != "exam" and is_ec(item["name"], settings["ec_keywords"]),
            "close": item["close"], "open_str": _fmt_date(item["open"]),
            "close_str": _fmt_date(item["close"]), "time_str": _fmt_time(item["close"]),
            "completed": bool(done), "moodle_completed": bool(item["completed"]),
            "manual_exam": bool(item.get("manual_exam")), "optional_reason": reason,
            "status": open_status(item["open"], item["close"], now_ts),
            "date_tbc": item["kind"] == "exam" and not item["close"], "auto": item.get("auto", False),
            "hint": item.get("hint"),
            "description": item.get("description") or "", "url": item.get("url"),
            "countdown": countdown(item["close"], now_ts), "open_full": _fmt_full(item["open"]),
            "days_left": days_left(item["close"], now_ts)[0], "urgency": days_left(item["close"], now_ts)[1],
            "close_full": _fmt_full(item["close"]),
            "expected": datetime(*_hint_key(item.get("month"), now), 1).strftime("%B %Y")
            if not item["close"] and item.get("month") else None,
            "month_key": _month_key(item["close"]) if item["close"] else _hint_key(item.get("month"), now),
        }
        if row["date_tbc"]:
            row["close_str"], row["time_str"] = "Date TBC", "—"
        if reason:
            module["optional"].append(row)  # listed in the module view only, with a "Counts" button
            continue
        module["items"].append(row)
        rows.append(row)

    visible = [r for r in rows if show_ec or not r["ec"]]
    # Upcoming: due from now on, plus exams with no date yet whose files name a month.
    upcoming = [r for r in visible if not r["completed"] and (
        (r["close"] and r["close"] >= now_ts) or (r["date_tbc"] and r["month_key"]))]
    exams_tbc = [r for r in visible if r["date_tbc"] and not r["completed"]]  # listed below the months
    # Past its closing date and not done (EC versions excluded - those aren't mine).
    overdue = sorted((r for r in rows if not r["ec"] and not r["completed"] and r["close"] and r["close"] < now_ts),
                     key=lambda r: r["close"], reverse=True)

    for module in modules.values():
        module["left"] = sum(
            1 for r in module["items"]
            if not r["ec"] and not r["completed"] and (r["close"] is None or r["close"] >= now_ts)
        )
        module["items"].sort(key=lambda r: (r["close"] is None, r["close"] or 0))
        module["optional"].sort(key=lambda r: (r["close"] is None, r["close"] or 0))

    # Month columns: the current month through the last month with something due.
    start = (now.year, now.month)
    end = max([r["month_key"] for r in upcoming] + [start])
    months, key = [], start
    while key <= end:
        months.append({
            "label": datetime(key[0], key[1], 1).strftime("%B %Y"),
            "rows": sorted((r for r in upcoming if r["month_key"] == key),
                           key=lambda r: (r["close"] is None, r["close"] or 0)),  # "Date TBC" last
        })
        key = _next_month(key)
    this_month_rows = months[0]["rows"]
    # A month with nothing left to do (all completed, or nothing due) isn't shown.
    months = [m for m in months if m["rows"]]

    completed = sorted((r for r in visible if r["completed"]), key=lambda r: r["close"] or 0, reverse=True)

    counted_upcoming = [r for r in upcoming if not r["ec"]]
    stats = {
        "today": now.strftime("%A %d %B"),
        "open_now": sum(1 for r in counted_upcoming if r["status"] == "open"),
        "this_month": len([r for r in this_month_rows if not r["ec"]]),
        "next": min((r for r in counted_upcoming if r["close"]), key=lambda r: r["close"], default=None),
    }

    overdue_modules = {r["module_id"] for r in overdue}
    for module in modules.values():
        # Shown on the dashboard only while there's something left to do in it.
        module["active"] = module["left"] > 0 or module["id"] in overdue_modules

    return {
        "stats": stats,
        "modules": sorted(modules.values(), key=lambda m: m["code"]),
        "months": months,
        "max_rows": max([len(m["rows"]) for m in months] + [1]),  # keeps every month table the same height
        "completed": completed,
        "exams_tbc": exams_tbc,
        "overdue": overdue,
    }
