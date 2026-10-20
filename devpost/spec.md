---
doc: spec
status: approved
---

# Crunch — Technical Spec

## How This Works, In Plain Language
The app is a small **Python program using Flask** that runs on my laptop. I open `http://localhost:5000` in my browser and Flask sends back the dashboard as a web page.

When the page loads, Flask **asks Moodle for my data** using my personal **key (token)**, kept in a `.env` file that git ignores. It's like posting a form to Moodle's office: the request says "this is me" (the key) and "what I want" (the function name, e.g. *my in-progress courses*), and Moodle replies with **JSON**, which Python turns into lists and dictionaries. The browser never sees the key — the browser talks to Flask, Flask talks to Moodle.

Flask then **merges** Moodle's assessments with my own notes — weights, "Doesn't count" marks, manual ticks, and exams I've added — which live in a small **JSON file** (`data/tracker.json`), like a notebook the app keeps. It hides last year's modules, hides EC/extra-time versions (spotted by keywords in brackets like "(Extra Time,SSP)"), works out priority from weight, groups everything by the month it closes, and fills in the page.

If Moodle can't be reached, it uses a saved copy of the last successful answer (`data/moodle_cache.json`) and shows "Offline — assessments unable to update."

Why this shape: one program, one notebook file, one outside service. No database, no login system, no hosting — nothing that doesn't help prove the idea.

## The Core Journey Through the System
PRD ref: `prd.md > The Core Journey`.
1. I open `localhost:5000` → Flask's dashboard route runs.
2. **Moodle client** asks Moodle for: who I am → my in-progress courses → quizzes and assignments in those courses → whether each is completed. It saves the answer to `moodle_cache.json`. (If it fails → loads the cache and sets the offline flag.)
3. **Tracker logic** merges in `tracker.json`: drops "Doesn't count" items, adds my manual exams, attaches weights, sets priority (≤10 Low, ≤50 Medium, >50 High, none → ⚠ Needs weight), flags EC versions, marks completed items (Moodle says so, or I ticked it).
4. Flask renders `dashboard.html`: module summary (remaining count per module) + month columns (current month onward), each a table of rows. EC rows only appear if the URL has `?ec=1` (the EC button toggles this).
5. I click a module → `module.html` lists its assessments with a weight box, a "Doesn't count" button, a "Mark done" tick, and the Add exam form. Submitting any of these is a normal HTML form → Flask updates `tracker.json` → redirects back.
6. I complete a quiz on Moodle → I reload the dashboard → step 2 now reports it finished → it moves to `completed.html` and the module count drops.

## Stack
- **Python 3.11+** — learner's existing language; new learning is the web side, not the language.
- **Flask 3.x** — small web framework; serves pages and handles form submissions. Docs: https://flask.palletsprojects.com/
- **Jinja2** (comes with Flask) — HTML templates with `{{ placeholders }}` filled from Python. Docs: https://jinja.palletsprojects.com/
- **requests** — makes the web calls to Moodle. Docs: https://requests.readthedocs.io/
- **python-dotenv** — loads the key from `.env`. Docs: https://pypi.org/project/python-dotenv/
- **pypdf** — reads text from module PDFs for automatic weights (added in slice 7). Docs: https://pypdf.readthedocs.io/
- **truststore** — HTTPS via the Windows certificate store (added in slice 1). Docs: https://truststore.readthedocs.io/
- **pytest** — tests for the pure logic (priority, EC detection, month grouping). Docs: https://docs.pytest.org/
- **Plain HTML + CSS**, almost no JavaScript — forms and links do the work, keeping the browser side simple.

Learner agreed to Python + Flask (tradeoff accepted: some HTML/CSS needed for the look). Versions were not looked up during planning — pin whatever `pip install` gives in `requirements.txt` at build step 1.

## Where It Runs and How Someone Tries It
- Runs locally on Windows; needs Python 3.11+.
- Setup: `python -m venv .venv`, `.venv\Scripts\activate`, `pip install -r requirements.txt`, copy `.env.example` to `.env` and fill in `MOODLE_URL` and `MOODLE_TOKEN` (from Moodle → Preferences → Security keys, "Moodle mobile web service"). **Never commit `.env` or paste the key into chat.**
- Start: `python app.py`, then open `http://localhost:5000`.
- Demo recording: screen-record the browser — dashboard, module view (enter a weight, priority colour changes), EC toggle, add exam, then complete/reload to show it move to Completed.
- **No deployment** — the app holds a personal Moodle key; a public site would expose it. Submission = demo video + public GitHub repo (without `.env` or `data/`).

## Look and Feel
From `prd.md > Look and Feel`:
- **Dark theme**: near-black/charcoal background, slightly lighter panels for the module summary and month columns, light grey text. One accent colour inspired by City St George's for headings/links — pick from the university's public site during the build; no logo or official branding.
- **Clean, enhanced-Moodle feel**: plenty of spacing, clear tables, a readable sans-serif system font (e.g. `Segoe UI, system-ui, sans-serif`), no clutter.
- **Priority badges**: red High, yellow Medium, green Low — coloured pill labels tuned to stay readable on dark backgrounds.
- **⚠ Needs weight**: red-outlined label with the ⚠ icon, visually distinct from the solid red High badge.
- **EC rows** (when shown): small "EC / Extra time" tag, slightly dimmed.
- Month columns side by side; scroll sideways when there are more months than fit.
- Interface copy: short and plain ("3 left", "No assessments", "Offline — assessments unable to update").

## Components

### Moodle Client (`moodle_client.py`)
Sends web service calls to Moodle and returns plain Python data. Knows nothing about weights or priority.
- `call(function, **params)` — one request to `/webservice/rest/server.php`; raises a clear error if Moodle returns an `exception` field.
- `fetch_snapshot()` — runs the calls in **External Services** and returns `{courses, assessments}` with each assessment as `{id, course_id, module_name, name, kind ("quiz"/"assign"), open, close, completed}`.
PRD ref: `prd.md > Loading Assessments From Moodle`, `prd.md > Completion`.

### Storage (`storage.py`)
Reads and writes `data/tracker.json` and `data/moodle_cache.json`; creates them empty if missing.
PRD ref: `prd.md > States and Boundaries` (persists between sessions; offline).

### Tracker Logic (`tracker.py`)
Pure functions, no web calls — this is what the tests cover.
- `priority(weight)` → `"high" | "medium" | "low" | None`. Implements `prd.md > Weights and Priority`.
- `is_ec(name, keywords)` → true if the name contains any keyword as whole words (case-insensitive). Implements `prd.md > EC and Extra-Time Versions`.
- `assessment_type(item, type_keywords)` → "Quiz" / "Coursework" / "Viva" / "Exam"… from Moodle kind plus name keywords. Implements `prd.md > Assessment Rows`.
- `build_view(snapshot, tracker, show_ec)` → modules with remaining counts, months (current month onward, by closing date) with rows, and the completed list. Drops "Doesn't count" items; adds manual exams. Implements `prd.md > Excluding Non-Contributing Assessments`, `prd.md > Adding Exams`.

### Web App (`app.py`)
Flask routes:
- `GET /` — dashboard. `?ec=1` shows EC rows. Implements `prd.md > Screens and Layout`.
- `GET /module/<course_id>` — module view.
- `GET /completed` — completed list.
- `POST /assessment/<id>/weight` — save weight.
- `POST /assessment/<id>/exclude` — mark "Doesn't count."
- `POST /assessment/<id>/tick` — manual done/undone.
- `POST /module/<course_id>/exam` — add exam.
Each POST updates `tracker.json` then redirects back (no page JavaScript needed).

### Templates and Styles (`templates/`, `static/style.css`)
`base.html` (layout, nav: Dashboard · Completed, offline banner), `dashboard.html`, `module.html`, `completed.html`; one stylesheet implementing **Look and Feel**.

### Weight Finder (`weight_finder.py`)
Added during the build (slice 7). Finds assessment weights in each module's Moodle content.
- Pure part (tested): `find_weights(text, source)` pulls "weight findings" (label text before a %, the %, type such as coursework/quiz/exam/assessment, number, and whether it's a per-item or combined figure) from lines that mention an assessment word and skips noise (pass marks, pass rates, "longer time"). `match(findings, items)` pairs findings with assessments by type + number (e.g. "CW 1 (Analysis) … 45%" ↔ "Coursework 1 (Analysis) Submission Area"); per-item figures ("each … 2.5%") beat combined ones.
- Fetch part: `core_course_get_contents` → section summaries, labels and pages as text, plus PDFs whose name looks like an overview/intro/module spec/assessment schedule (downloaded in memory with the token; read with `pypdf`).
- Runs automatically in a background thread (it downloads a few MB, so not inside a page load): started when a page loads and a module has never been scanned, or has an unweighted assessment and hasn't been scanned for a day. While it runs the page shows "Finding weights…" and refreshes itself. Results are saved in `tracker.json`.
PRD ref: `prd.md > Weights and Priority`.

### Settings (`settings.json`)
Editable without touching code:
- `module_code_pattern` — a course counts as a current module only if its name starts with a module code (default `^[A-Z]{2}\d{4}`, e.g. "IN2002 …"); filters out in-progress non-module sites like Library Induction.
- `ec_keywords` — matched anywhere in the name, case-insensitive, whole words (`["extra time", "ssp", "extenuating circumstances", "extension", "extensions"]`).
- `type_keywords` (e.g. `{"viva": "Viva", "exam": "Exam"}`).

## Data Model
**`data/tracker.json`** (my notes — lives on my laptop, updated by the module-view forms, read on every page load, survives restarts):
```json
{
  "assessments": {
    "quiz-123": { "weight": 2.5, "excluded": false, "manual_done": false },
    "assign-45": { "weight": 30, "excluded": false, "manual_done": false }
  },
  "exams": [
    { "id": "exam-1", "course_id": 12, "name": "DSA Exam", "close": "2027-01-14T09:30", "weight": 70, "done": false }
  ]
}
```
IDs are `"<kind>-<moodle id>"` so quizzes and assignments never collide.

**`data/moodle_cache.json`** — last successful `fetch_snapshot()` result plus `fetched_at`; overwritten on each successful load, read only when Moodle fails.

**Not stored**: priority, month grouping, counts — recalculated each load from the above.

Completed = Moodle says completed **or** `manual_done`/`done` is true.

## File Structure
```
assessment-tracker/
├── app.py               # Flask routes: pages + form handlers
├── moodle_client.py     # talks to Moodle with the token
├── tracker.py           # pure logic: priority, EC detection, types, month view
├── storage.py           # read/write data/*.json
├── settings.json        # EC keywords, type keywords (editable)
├── templates/
│   ├── base.html        # layout, nav, offline banner
│   ├── dashboard.html   # module summary + month columns
│   ├── module.html      # weights, Doesn't count, tick, Add exam
│   └── completed.html   # completed assessments
├── static/
│   └── style.css        # dark theme, priority badges
├── tests/
│   └── test_tracker.py  # priority thresholds, EC detection, month grouping
├── scripts/
│   └── check_moodle.py  # step-1 connection check: prints site info, courses, activity types
├── data/                # personal data — gitignored
│   ├── tracker.json
│   └── moodle_cache.json
├── requirements.txt
├── .env.example         # MOODLE_URL=, MOODLE_TOKEN= (no real values)
├── .gitignore           # already ignores .env and learner profile; add /data/
├── README.md
└── devpost/             # Devpost learning workspace
```

## External Services and Dependencies

### Moodle Web Services (REST)
- Endpoint: `GET {MOODLE_URL}/webservice/rest/server.php?wstoken={TOKEN}&wsfunction={FUNCTION}&moodlewsrestformat=json&{params}`
- Auth: the personal "Moodle mobile web service" token. Free; no published rate limit for normal use — we make a handful of calls per page load.
- Errors come back as JSON with `exception`, `errorcode`, `message`.
- Docs: https://docs.moodle.org/dev/Web_service_API_functions and https://docs.moodle.org/dev/Creating_a_web_service_client

Calls (from memory of the Moodle API — **not verified against this Moodle; `check_moodle.py` confirms them at build step 1**):

| Purpose | Function | Key params | Fields used |
|---|---|---|---|
| Who am I | `core_webservice_get_site_info` | — | `userid`, `sitename` |
| Current modules | `core_course_get_enrolled_courses_by_timeline_classification` | `classification=inprogress` | `courses[].id, fullname, shortname` |
| Quizzes | `mod_quiz_get_quizzes_by_courses` | `courseids[0]=…` | `quizzes[].id, course, name, timeopen, timeclose` |
| Coursework | `mod_assign_get_assignments` | `courseids[0]=…` | `courses[].assignments[].id, name, allowsubmissionsfromdate, duedate` |
| Quiz completed? | `mod_quiz_get_user_attempts` | `quizid`, `status=finished` | `attempts[]` non-empty → done |
| Coursework completed? | `mod_assign_get_submission_status` | `assignid` | `lastattempt.submission.status == "submitted"` → done |

Times are Unix timestamps → converted to local dates/times for display.

## Important Failure Modes
- **Moodle unreachable / token rejected** → load `moodle_cache.json`, show "Offline — assessments unable to update" banner. If there's no cache yet, show the banner and an empty dashboard.
- **A completion call fails or is not allowed** → treat that item as not completed; the manual tick still works (PRD fallback).
- **An assessment has no closing date** → shown only in its module view, labelled "No closing date," not in the month columns.

## What Was Simplified and Why
- **Manual weights** instead of reading module slides — agreed in scope; slides vary too much.
- **Refresh on page load** instead of background syncing — same result, simpler, visible timing.
- **JSON file** instead of a database — one user, a few dozen items. Learner agreed.
- **HTML forms + redirects** instead of a JavaScript front end — fewer moving parts.
- **Local only**, no deployment — protects the personal token.
- **Quizzes and assignments only** from Moodle (plus manual exams) — covers what the learner described.

## Decisions and Open Issues

### Decisions
- Python + Flask local web app — learner agreed (knows Python; accepts some HTML/CSS).
- Moodle web services with personal token — learner confirmed a "Moodle mobile web service" key exists.
- JSON file storage — learner agreed.
- Add-exam feature — learner chose to add it (exams aren't on Moodle); PRD updated with `prd.md > Adding Exams`.
- EC detection by bracketed keywords, keywords in `settings.json` — based on learner's real example "Quiz 1 on Lecture 1 and 2 (Extra Time,SSP)" and "it can vary."
- Implementation details derived from these (agent): forms + redirects, cache file, ID format, month columns from current month onward.

### Learner's useful unknown
**"How the app talks to Moodle with the key."** Explained during planning: a request to `server.php` carrying `wstoken` (identity), `wsfunction` (the question), and `moodlewsrestformat=json`; Moodle replies with JSON; Flask sits in the middle so the browser never sees the key. **Build step 1** makes it concrete: `scripts/check_moodle.py` calls `core_webservice_get_site_info` and prints the reply, so the learner sees a real request and response.

### Open issues (check at build step 1)
- Confirm each function in the table is allowed for this token and returns the expected fields.
- **Does coursework use Moodle Assignment, or something else like Turnitin?** If coursework doesn't appear via `mod_assign_get_assignments`, `check_moodle.py` will list the activity types present and we'll adapt the client before building further.
- Overdue, not-completed items from past months: not shown in the month columns for the PoC (they remain in the module view). Revisit if it feels wrong when using it.
