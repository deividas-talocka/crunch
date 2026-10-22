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

- [x] **4. EC button and Add exam**
  Becomes usable: The EC button shows/hides EC/extra-time versions with a label; in a module you can add an exam (name, date, time, weight) and it appears in the right month with its priority.
  Why now: Completes the "what's coming up" picture — exams are the highest-weight items — once the core view and priority exist.
  PRD ref: `prd.md > EC and Extra-Time Versions`, `prd.md > Adding Exams`
  Spec ref: `spec.md > Components` (Web App `?ec=1`, `POST /module/<id>/exam`, Tracker Logic `build_view`), `spec.md > Data Model` (`exams`)
  Build: `?ec=1` toggle and labelled EC rows; Add exam form and route; manual exams merged into `build_view`; test that an added exam lands in its month.
  Verify (mechanical): `pytest` passes; `/` hides EC names, `/?ec=1` shows them with the label; add an exam via the form and confirm it's in `tracker.json` and in the correct month column with the right badge.
  Learner check: Press the EC button and back; add your DSA exam with a January date and 70% — does it show in January as red High?
  Commit: `Add EC toggle and manual exams`

- [x] **5. Completed assessments move out by themselves**
  Becomes usable: After you finish a quiz or submit coursework on Moodle, reloading moves it to the Completed page and the module's "left" count drops. Manual tick works for exams and anything Moodle can't report.
  Why now: The demo's "oh, that's cool" moment, built on everything above.
  PRD ref: `prd.md > Completion`, `prd.md > Adding Exams`, `prd.md > The Core Journey` (step 6)
  Spec ref: `spec.md > External Services and Dependencies` (completion calls), `spec.md > Components` (Moodle Client, Web App tick route, `completed.html`), `spec.md > Important Failure Modes`
  Build: Completion calls in `fetch_snapshot()` (failures → not completed); `POST .../tick`; `GET /completed` and template; counts exclude completed; nav link.
  Verify (mechanical): Run the snapshot and confirm completed flags match at least one item you know you've done; tick an item and confirm it moves to `/completed` and the count drops; untick restores it.
  Learner check: Check an assessment you've already completed shows under Completed, and tick/untick an exam to see it move.
  Commit: `Add completion detection and Completed page`

- [x] **6. Offline still shows your assessments**
  Becomes usable: If Moodle can't be reached, the dashboard still shows the last-loaded assessments under "Offline — assessments unable to update." A README explains setup and running.
  Why now: Last, because it's a fallback around the working journey; also readies the repo for the demo.
  PRD ref: `prd.md > States and Boundaries` (offline)
  Spec ref: `spec.md > Components` (Storage cache), `spec.md > Important Failure Modes`, `spec.md > Where It Runs and How Someone Tries It`
  Build: Save `moodle_cache.json` on success, load it on failure with offline banner; README with setup/run steps.
  Verify (mechanical): Run with a deliberately wrong `MOODLE_URL` via an environment override and confirm the banner plus cached rows appear; restore and confirm the banner is gone.
  Learner check: Turn off Wi-Fi, reload the dashboard, and confirm you see the offline message with your assessments still there.
  Commit: `Add offline fallback and README`

- [x] **7. Weights fill themselves in**
  Becomes usable: The app finds weights by itself — no button. In the background (first run, and whenever a module has an unweighted assessment not checked in the last day) it reads each module's Moodle page text and intro/spec/schedule PDFs, fills in weights with their source shown ("45% · from L0_Intro_City2026.pdf"), lists anything it found but couldn't match (e.g. "Examination 70%"), and uses a found exam weight when you add an exam without one. A small "edit" link keeps manual correction as a backup.
  Why now: Learner chose to bring the deferred auto-weights feature into the PoC after the investigation found weights for all four modules; built on the finished core.
  PRD ref: `prd.md > Weights and Priority`
  Spec ref: `spec.md > Components` (Weight Finder), `spec.md > External Services and Dependencies`, `spec.md > Data Model`
  Build: `weight_finder.py` (pure: extract weight findings from text, match them to assessments; fetch: gather page text and selected PDFs via `core_course_get_contents` + token file download, `pypdf`); background scan started from page loads when needed, with a "Finding weights…" note and self-refresh while it runs; store `weight`, `weight_source`, and per-module findings in `tracker.json`; never overwrite a weight I typed; module view shows source + edit; tests using the real sentences found.
  Verify (mechanical): `pytest` passes (extraction + matching on the real lines); run the finder against real Moodle with temp storage and confirm IN2013 Quiz 1 = 2.5, Coursework 1 = 45, IN2015 Assessment 1 = 40, Assessment 2 = 60, and "Examination 70%" listed for IN2029; a typed weight is not overwritten.
  Learner check: Open the dashboard, wait for the "Finding weights…" note to clear, and check the colours and sources match your modules' real weights.
  Commit: `Find weights automatically from module pages and PDFs`

## Hands-on Checkpoints

- [x] Early usable behavior explored — after slice 3 (real dashboard with priority colours): feedback on look and behavior shapes slices 4–6
- [x] Final kick-the-tires exploration and feedback completed

## Final Review

- [x] No opening date shows a red "not open yet" light (learner: "no opening date means it's not out yet") — verified: IN2015 Assessment 1 now red; tests pass.
- [x] Exams found in module files are added automatically (learner: "find out all the exams and add it to the modules") — verified on real data: IN2002 Exam 70% in January as Date TBC, IN2029 Exam 70% under "date to confirm"; setting a date moves it into its month; no duplicates on reload; tests pass.
- [x] IN2002 viva was missing (learner: "its missing the viva for in2002") — its sentence wraps across two PDF lines and "coursework"/"tutorials" won over "viva". Finder now joins wrapped lines, prefers specific words (viva/oral/exam), and adds vivas like exams. Verified on real data: "IN2002 Viva · 30%" added with hint "throughout week 10"; tests pass.
- [x] App renamed to **Crunch** (learner chose it from suggestions) — top bar, page titles, README, plan docs.
- [x] "Date to confirm" exams moved below the monthly tables and list every exam/viva without an exact date ("Expected January 2027" where the file names a month) — learner request. Found and fixed a template break during this change; added tests/test_pages.py so every page is rendered in the tests. Verified by screenshot on real data; 28 tests pass.
- [x] Logo in the top bar; Add exam form removed (set date kept); unreleased coursework from module files added as placeholders that disappear once Moodle posts the real one (learner: "IN2029 is missing the coursework with 30%") — verified on real data: IN2029 Coursework 30% and IN2013 Coursework 2 45% shown under "Coming up — date to confirm"; 29 tests pass.
- [x] Months with nothing left to do are removed (learner: "if i was to complete all the assessments in a specific month it would remove that month"); "Nothing coming up" when all are done — 31 tests pass, real dashboard checked.
- [x] ⏮ First / Last ⏭ buttons beside Previous/Next (learner request) — 32 tests pass; on real data Last jumps to Dec 2026–Jan 2027.
- [x] Assessment page (click any name: details, countdown, Moodle description, actions, Open in Moodle) and Overdue area above the months (learner requests) — 40 tests pass; detail page checked by screenshot on real data; no overdue items currently, so the area is hidden.
- [x] "Open module in Moodle" button on each module page (learner request) — links to /course/view.php?id=<module>; 41 tests pass; real link checked.
- [x] More interesting background: slow-drifting blue/purple/teal glows and a faint fading dot grid, CSS only, still when reduced motion is on (learner request: keep everything else) — checked by screenshot.
- [x] Slogan "What matters when crunch time hits" beside the logo (learner picked it over "Your assessments, ranked by what matters") (replacing "for City St George's students"); "Completed" renamed "Completed assessments" in the nav and page (learner request) — 41 tests pass.
- [x] Quizzes with no closing date explained as "Optional practice quiz — no closing date, so it isn't assessed" (learner request for IN2002) — 41 tests pass; real IN2002 page checked.
- [x] Modules with nothing left to do are hidden from the dashboard (learner: "so its purely focused on whats left to do"); overdue work keeps a module visible; "Every module is done" message — 42 tests pass; all four real modules still have work, so all show.
- [x] Days left before each deadline in the month tables and the Next deadline tile, coloured by urgency (≤2 days red, ≤7 amber) — learner request; 43 tests pass; checked by screenshot.
- [x] Top bar redesign: glassier bar with gradient glow line, larger logo and name with divided italic slogan, pill tabs with the current page highlighted, completed-count bubble (learner request) — 43 tests pass; checked by screenshot on two pages.
- [x] Overdue work now counts in a module's "left" number (learner agreed) — 43 tests pass.
- [x] Free rule-based "Ask Crunch" helper in a right-edge sidebar with three questions (learner chose option 1: no AI service) — tests/test_helper.py; 48 tests pass; checked open and closed by screenshot on real data.
- [x] Footer: logo + slogan, "Updated from Moodle <time>" ("Last loaded" when offline), "Made by Deividas", optional GitHub link via settings.json github_url (fill in during 6-ship), and an unofficial / not-affiliated note — learner agreed; 49 tests pass; checked by screenshot.
- [x] Final review complete — feedback resolved and learner confirms ready to ship ("i think its ready"); 49 tests pass

## Code Tour and App Map

- [x] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [x] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [x] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: Guided route on the spec's recorded unknown ("how the app talks to Moodle with the key"), following a dashboard reload through three real code locations. Learner reviewed the route and replied "looks great"; individual stops were not separately confirmed.
Route and stops: app.py `def load_view` → moodle_client.py `def call` (wstoken / wsfunction / moodlewsrestformat) → moodle_client.py `def _completed` → tracker.py `build_view`.
Edit outcome: Offered (change the helper greeting in templates/base.html); not made — no working-tree changes.
Reflection: Offered and answered (kept in the ignored learner profile).
Activity mode: Live app and editor (learner's own); agent verified map anchors against source and rendered the map offline.

## Revisions

- Added `truststore` so HTTPS uses the Windows certificate store — `requests`' bundled certificates couldn't verify `moodle4.city.ac.uk` (SSL CERTIFICATE_VERIFY_FAILED).
- Added `scripts/save_token.py` (token via the Moodle app launch page) — City uses single sign-on, so Security keys only showed an RSS key; the mobile web service token is created by the app's launch flow.
- "Current modules" = in-progress courses whose name starts with a module code (`settings.json > module_code_pattern`) — Moodle's "in progress" also includes non-module sites (Library Induction, Academic Skills, etc.).
- EC detection matches keywords anywhere in the name, not only in brackets — real names include "(Extenuating Circumstances and extensions)" and "- Extenuating Circumstances and extensions".
- Checkpoint feedback (after slice 3): month view uses ◀/▶ buttons with two months at a time instead of a sideways scroll; month tables padded to equal height; optional assessments detected automatically (no closing date, "formative"/"practice"/"optional" in the name, or "no mark"-style description) and listed in the module view with a "Counts" override — learner: "DSA quizzes are optional", "the formative activity is not an assessment". Moodle descriptions didn't reliably say "optional", hence the combined rule. PRD updated.
- Completion calls run in parallel and only for assessments that have opened; `fetch_snapshot` now takes the module-code pattern so it only queries real modules — one call per assessment took ~2.4s sequentially. Verified against real data: Moodle reports DSA Quiz 1 as finished.
- Added slice 7 (automatic weights) — learner asked to try it after the core; an investigation found weights for all four modules (IN2002 overview PDF, IN2013 intro PDF, IN2015 page label, IN2029 assessment schedule PDF). Learner chose fully automatic finding with no button ("always find the weights by itself"), so it runs in the background when needed; manual entry kept as a small "edit" backup on the agent's recommendation, which the learner accepted. Moved from `scope.md > Later` into the PoC.
- Confirmed: coursework is Moodle Assignment (no Turnitin); all planned functions answered with this token. DSA quizzes have no closing date → module view only, per `spec.md > Important Failure Modes`.
- Added "marks so far" during 6-ship (learner chose to build it now over deferring) — Moodle shares grades via `gradereport_user_get_grade_items` (checked: 1 released grade in IN2013 at the time); module cards show earned/assessed marks, Completed shows grades, exams/vivas take a typed mark. 52 tests pass; checked on real data.
- Marks shown out of the whole module (100%) with the 40% pass mark (`settings.json > pass_mark`) as a line on the bar and "X% more to pass" — learner request, replacing the per-graded-work average. 52 tests pass; checked on real data.
- Marks bar shown on every module card, including modules with no released marks yet ("0% of 100% so far · 40% more to pass") — learner request. 52 tests pass; checked on real data.
