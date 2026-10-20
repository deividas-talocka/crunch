# Assessment Tracker

A focused view of my upcoming university assessments, pulled from Moodle, with the noise stripped out and ranked by how much they're worth.

Moodle's dashboard timeline mixes everything together: last year's modules, EC / extra-time duplicates, practice quizzes. This app shows only the assessments that count for this year's modules, month by month, with a colour-coded priority from each assessment's weight:

- **Current modules only.** Courses whose name starts with a module code (e.g. `IN2013 …`).
- **EC / extra-time versions are hidden**, with a button to show them, labelled.
- **Optional work is left out automatically.** That means no closing date, "formative" / "practice" in the name, or a description like "no mark". Each module page lists what was left out and why, with a **Counts** button.
- **Weights are found automatically.** In the background, the app reads each module's Moodle page and its overview / module spec / assessment schedule PDFs, and fills in weights with their source (e.g. "45% · from L0_Intro_City2026.pdf"). A small edit link corrects a misread, and a weight you type is never overwritten.
- **Priority from weight:** ≤10% green Low, ≤50% yellow Medium, above that red High.
- **Status lights:** green means open now, red means not open yet.
- **Completion is detected from Moodle.** A finished quiz attempt or a submitted coursework moves the assessment to **Completed**. Exams (which aren't on Moodle) can be added by hand and ticked off.
- **Offline:** if Moodle can't be reached, the last loaded assessments still show.

Built with Python, Flask and Moodle's web service API. It runs locally on your own computer.

## Setup (Windows)

Needs Python 3.11+.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set `MOODLE_URL` to your Moodle's address, e.g. `https://moodle.example.ac.uk` (no trailing slash).

### Getting your Moodle token

The app uses the same personal **"Moodle mobile web service"** token as the official Moodle app.

- **If your Moodle shows it** under *Preferences → Security keys*, copy that key into `MOODLE_TOKEN=` in `.env`.
- **If your university uses single sign-on** and only an RSS key is listed, use the Moodle app's sign-in page instead:
  1. Log in to Moodle in Edge or Chrome, press **F12** and open the **Network** tab (tick *Preserve log*).
  2. In the **address bar**, visit
     `https://<your-moodle>/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=12345&urlscheme=moodlemobile`
  3. Copy the `moodlemobile://token=…` address from the Network tab and save it as `data/launch.txt`.
  4. Run `python scripts/save_token.py`. It writes the token into `.env` and deletes `launch.txt`.

Treat the token like a password. Never commit `.env` or share the token. `.gitignore` already excludes `.env` and `data/`.

Check the connection:

```
python scripts/check_moodle.py
```

## Run

```
python app.py
```

Open http://localhost:5000.

## Tests

```
python -m pytest
```

## Settings

`settings.json` can be edited without touching code: the module-code pattern, EC keywords, optional-work keywords, and assessment-type keywords.

## Project layout

```
app.py              Flask routes: pages and form handlers
moodle_client.py    talks to Moodle with the token
tracker.py          pure logic: priority, EC and optional detection, month view
weight_finder.py    finds weights in module pages and PDFs (runs in the background)
storage.py          my notes (data/tracker.json) and the offline cache
templates/, static/ pages and the dark theme
scripts/            connection check and token helper
tests/              tests for tracker.py
devpost/            planning documents (scope, PRD, spec, build checklist)
```
