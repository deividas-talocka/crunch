---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. The app can talk to your Moodle and list your current modules**
  Becomes usable: A script you run that connects to Moodle with your key and prints who you are, your in-progress modules, and the quizzes/assignments it finds in each — real data on screen.
  Why now: The whole app depends on Moodle answering the way the spec assumes; this is the riskiest unknown, so we prove it before building anything on top. It's also the learner's chosen unknown — seeing a real request and reply. Includes project setup (venv, dependencies, `.gitignore` for `data/`).
  PRD ref: `prd.md > Loading Assessments From Moodle`, `prd.md > Open Questions`
  Spec ref: `spec.md > External Services and Dependencies`, `spec.md > Components` (Moodle Client), `spec.md > Decisions and Open Issues`
  Build: Create venv and `requirements.txt` (flask, requests, python-dotenv, pytest); add `/data/` to `.gitignore`; write `moodle_client.py` with `call()`; write `scripts/check_moodle.py` that calls site info, in-progress courses, quizzes, assignments, and prints names/dates plus any activity types that don't fit (e.g. Turnitin).
  Verify (mechanical): Run `scripts/check_moodle.py`; confirm it exits without error, prints a site name, at least one in-progress course, and quiz/assignment entries with dates. Record any function that's refused or any unexpected activity type under Revisions.
  Learner check: Run `python scripts/check_moodle.py` and say whether the modules listed are exactly this year's and the assessments look like what you see on Moodle.
  Commit: `Add Moodle client and connection check`

- [x] **2. The dashboard shows this year's real assessments, month by month**
  Becomes usable: Open `localhost:5000` and see a dark dashboard: module summary with "left" counts, and side-by-side month columns (current month onward) with a table row per assessment — module, name, type, open/close dates, close time — every row showing "⚠ Needs weight". EC/extra-time versions are already hidden.
  Why now: First half of the kernel — the noise filtering (current modules only, EC hidden) — on the real screen, so you can react to the look early.
  PRD ref: `prd.md > The Core Journey` (steps 1–3), `prd.md > Screens and Layout`, `prd.md > Assessment Rows`, `prd.md > EC and Extra-Time Versions`, `prd.md > Look and Feel`, `prd.md > States and Boundaries` (first use, empty month)
  Spec ref: `spec.md > Components` (Moodle Client `fetch_snapshot`, Tracker Logic, Web App, Templates and Styles, Settings), `spec.md > Look and Feel`, `spec.md > Data Model`
  Build: `fetch_snapshot()`; `tracker.py` with `is_ec`, `assessment_type`, `build_view` (month grouping by closing date, no-closing-date items excluded from months); `settings.json`; `app.py` `GET /`; `base.html`, `dashboard.html`, `style.css`; `tests/test_tracker.py` for EC detection and month grouping.
  Verify (mechanical): `pytest` passes; start the app, fetch `/` and confirm 200 with month headings and assessment rows; confirm no names containing "(Extra Time" appear.
  Learner check: Open `http://localhost:5000` — are these the assessments you expect for this month and next, are last year's modules gone, and does the look feel like the "enhanced Moodle" you pictured?
  Commit: `Add dashboard with monthly assessment view`

- [x] **3. Weights turn into colour-coded priority**
  Becomes usable: Click a module, type weights (e.g. 2.5, 30), or mark an item "Doesn't count"; back on the dashboard, rows show green Low / yellow Medium / red High, and excluded items are gone. Weights survive a restart.
  Why now: The second half of the kernel — prioritising by weight — and the first data you save.
  PRD ref: `prd.md > Weights and Priority`, `prd.md > Excluding Non-Contributing Assessments`, `prd.md > The Core Journey` (steps 4–5)
  Spec ref: `spec.md > Components` (Storage, Tracker Logic `priority`, Web App weight/exclude routes), `spec.md > Data Model`
  Build: `storage.py` for `tracker.json`; `priority()`; `GET /module/<id>`, `POST .../weight`, `POST .../exclude`; `module.html`; priority badges in CSS; tests for thresholds (2.5→low, 10→low, 30→medium, 50→medium, 70→high, none→None).
  Verify (mechanical): `pytest` passes; post a weight via the app, confirm `data/tracker.json` contains it and the dashboard row shows the right badge; restart and confirm it's still there; exclude an item and confirm it's gone from `/`.
  Learner check: Open a module, enter the real weights for one module, mark an optional quiz "Doesn't count", and check the dashboard colours match what you'd expect.
  Commit: `Add weights, priority, and exclusion`

- [ ] **4. EC button and Add exam**
  Becomes usable: The EC button shows/hides EC/extra-time versions with a label; in a module you can add an exam (name, date, time, weight) and it appears in the right month with its priority.
  Why now: Completes the "what's coming up" picture — exams are the highest-weight items — once the core view and priority exist.
  PRD ref: `prd.md > EC and Extra-Time Versions`, `prd.md > Adding Exams`
  Spec ref: `spec.md > Components` (Web App `?ec=1`, `POST /module/<id>/exam`, Tracker Logic `build_view`), `spec.md > Data Model` (`exams`)
  Build: `?ec=1` toggle and labelled EC rows; Add exam form and route; manual exams merged into `build_view`; test that an added exam lands in its month.
  Verify (mechanical): `pytest` passes; `/` hides EC names, `/?ec=1` shows them with the label; add an exam via the form and confirm it's in `tracker.json` and in the correct month column with the right badge.
  Learner check: Press the EC button and back; add your DSA exam with a January date and 70% — does it show in January as red High?
  Commit: `Add EC toggle and manual exams`

- [ ] **5. Completed assessments move out by themselves**
  Becomes usable: After you finish a quiz or submit coursework on Moodle, reloading moves it to the Completed page and the module's "left" count drops. Manual tick works for exams and anything Moodle can't report.
  Why now: The demo's "oh, that's cool" moment, built on everything above.
  PRD ref: `prd.md > Completion`, `prd.md > Adding Exams`, `prd.md > The Core Journey` (step 6)
  Spec ref: `spec.md > External Services and Dependencies` (completion calls), `spec.md > Components` (Moodle Client, Web App tick route, `completed.html`), `spec.md > Important Failure Modes`
  Build: Completion calls in `fetch_snapshot()` (failures → not completed); `POST .../tick`; `GET /completed` and template; counts exclude completed; nav link.
  Verify (mechanical): Run the snapshot and confirm completed flags match at least one item you know you've done; tick an item and confirm it moves to `/completed` and the count drops; untick restores it.
  Learner check: Check an assessment you've already completed shows under Completed, and tick/untick an exam to see it move.
  Commit: `Add completion detection and Completed page`

- [ ] **6. Offline still shows your assessments**
  Becomes usable: If Moodle can't be reached, the dashboard still shows the last-loaded assessments under "Offline — assessments unable to update." A README explains setup and running.
  Why now: Last, because it's a fallback around the working journey; also readies the repo for the demo.
  PRD ref: `prd.md > States and Boundaries` (offline)
  Spec ref: `spec.md > Components` (Storage cache), `spec.md > Important Failure Modes`, `spec.md > Where It Runs and How Someone Tries It`
  Build: Save `moodle_cache.json` on success, load it on failure with offline banner; README with setup/run steps.
  Verify (mechanical): Run with a deliberately wrong `MOODLE_URL` via an environment override and confirm the banner plus cached rows appear; restore and confirm the banner is gone.
  Learner check: Turn off Wi-Fi, reload the dashboard, and confirm you see the offline message with your assessments still there.
  Commit: `Add offline fallback and README`

## Hands-on Checkpoints

- [x] Early usable behavior explored — after slice 3 (real dashboard with priority colours): feedback on look and behavior shapes slices 4–6
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence:
Route and stops:
Edit outcome:
Reflection:
Activity mode:

## Revisions

- Added `truststore` so HTTPS uses the Windows certificate store — `requests`' bundled certificates couldn't verify `moodle4.city.ac.uk` (SSL CERTIFICATE_VERIFY_FAILED).
- Added `scripts/save_token.py` (token via the Moodle app launch page) — City uses single sign-on, so Security keys only showed an RSS key; the mobile web service token is created by the app's launch flow.
- "Current modules" = in-progress courses whose name starts with a module code (`settings.json > module_code_pattern`) — Moodle's "in progress" also includes non-module sites (Library Induction, Academic Skills, etc.).
- EC detection matches keywords anywhere in the name, not only in brackets — real names include "(Extenuating Circumstances and extensions)" and "- Extenuating Circumstances and extensions".
- Checkpoint feedback (after slice 3): month view uses ◀/▶ buttons with two months at a time instead of a sideways scroll; month tables padded to equal height; optional assessments detected automatically (no closing date, "formative"/"practice"/"optional" in the name, or "no mark"-style description) and listed in the module view with a "Counts" override — learner: "DSA quizzes are optional", "the formative activity is not an assessment". Moodle descriptions didn't reliably say "optional", hence the combined rule. PRD updated.
- Confirmed: coursework is Moodle Assignment (no Turnitin); all planned functions answered with this token. DSA quizzes have no closing date → module view only, per `spec.md > Important Failure Modes`.

