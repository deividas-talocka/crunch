---
doc: prd
status: approved
---

# Crunch — Product Requirements

A dark, simplified "better Moodle" dashboard for me, a university student, that shows only my current modules' real assessments, month by month, prioritised by weight.
Source: `scope.md > The Unique Kernel`, `scope.md > The Core Loop`.

## The Core Journey
1. I open the app. It loads my assessments from Moodle (`scope.md > The POC Boundary`).
2. I see the **dashboard**: a **module summary** (each current module and how many assessments it has left) and the **month view** (months side by side, each with a table of that month's assessments).
3. New assessments without a weight appear in the month view with a red **⚠ Needs weight** label.
4. I click a module, see its assessments from Moodle, and enter a weight for each — or mark one **Doesn't count** (optional/practice) so it disappears.
5. Weighted assessments show a priority colour: red High, yellow Medium, green Low.
6. I do an assessment on Moodle (e.g. a quiz open 19–25 Oct). Next time the app checks Moodle, it detects completion and moves it to **Completed**; the module's "left" count drops. If completion can't be read from Moodle, I tick it manually instead.
7. Success: at a glance I know what's coming up this month and what matters most (`scope.md > What "Working" Looks Like`).

## Screens and Layout
- **Dashboard** (main screen)
  - **Module summary** — one entry per current module: module name + number of assessments left. Revised at final review: a module with nothing left to do (no upcoming, overdue, or date-to-confirm items) is hidden from the dashboard; its page remains.
  - **Month view** — two months side by side, each a month heading with a table of its assessments; **◀ Previous / Next ▶ buttons** move through the other months (revised at the build checkpoint: buttons instead of a sideways scroll). Every month's table is the same height, even when empty.
  - **EC button** — shows/hides EC and extra-time versions.
- **Module view** — opened by clicking a module (with an **Open module in Moodle** button for its resources, added at final review): lists that module's Moodle assessments, where I enter weights or mark "Doesn't count."
- **Completed** — a separate place holding all completed assessments for review.
- **Assessment page** (added at final review) — click any assessment name: module, type, weight and its source, priority, status light, full open/close dates with a countdown ("closes in 5 days"), Moodle's description (or the hint from module files), Mark done / Doesn't count / set date, and an **Open in Moodle** button.
- **Marks so far** (added during shipping) — every module card (0% until marks are released) shows marks earned from released grades × weights (e.g. "2.5% of 100% so far · 37.5% more to pass (40%)", with the pass mark marked on a progress bar; pass mark set in settings.json); grades come from Moodle for quizzes/coursework, and exam/viva marks can be typed on their assessment page. Completed assessments shows each grade. EC versions and optional work are left out.
- **Grade outlook** (added during shipping) — under the modules: "On track for <class>" from the average on marked work this year (all current modules counted equally), plus each band (1st 70%+, 2:1 60%+, 2:2 50%+, 3rd 40%+) with the average needed on remaining work, "✓ secured" or "out of reach". States how much of the year is marked and that it's an estimate, not the official degree classification. Bands in settings.json.
- **Footer** (added at final review) — logo and slogan, when the data was last updated from Moodle, "Made by Deividas Talocka" (plus a GitHub link once the repository exists), and "Built for Devpost's Build With AI: Basics hackathon."
- **Ask Crunch helper** (added at final review) — an "Ask Crunch" tab on the right edge of every page opens a sidebar with three questions: *What should I focus on this week?* (overdue first, then this week's work by weight, plus a nudge to start the next big piece early), *What's most important?* (top 5 still to do by weight), and *How am I doing?* (done vs total per module, overdue count). No AI model: plain rules over Crunch's own data — free, instant, private, works offline. Answers link to the assessment pages.
- **Overdue** (added at final review) — above the month tables, in red: past its closing date, not done, not optional, not EC; each with Mark done. Hidden when nothing is overdue.

## Look and Feel
- Influenced by City St George's, University of London: like an enhanced-looking Moodle — "easy to understand and simple."
- **Dark** theme.
- Priority colours: **red = High**, **yellow = Medium**, **green = Low**.
- "Needs weight" uses a distinct **⚠ label** (not just a red row) so it isn't confused with High priority.
- Inspired by the university's feel; not a copy of its logo or official branding.

## Features and Behavior

### Loading Assessments From Moodle
- Pulls assessments (name, module, type, opening date, closing date, closing time) from my Moodle.
- Shows only **current modules**; last year's modules never appear.
- [ ] Opening the app shows this year's modules only — no modules from last year.
- [ ] Each assessment's name, dates, and closing time match Moodle.

### Assessment Rows
Each row in the month view shows: **module, assessment name, weight, priority, opening date, closing date, closing time**. Type (quiz, exam, coursework, viva…) is shown too (`scope.md > The POC Boundary`).
- Each row shows **days left** before its deadline ("5 days left", "Tomorrow", "Today"), red within 2 days and amber within a week (added at final review).
- Each row also has a **status light** (added at the build checkpoint): green = open now and ready to do, red = not open yet (including anything with no opening date — final-review feedback: "no opening date means it's not out yet"). A legend explains it.
- [ ] Every assessment row shows all seven fields plus its type.
- [ ] A quiz open 19–25 Oct shows a green light on 20 Oct; one opening 2 Nov shows red.
- [ ] An assessment appears under the month of its closing date.

### Weights and Priority
- Revised during the build: weights are **found automatically, with no button**: in the background (on first run, and whenever a module has an unweighted assessment not checked in the last day) the app reads each module's Moodle page text and its intro / module spec / assessment schedule PDFs, fills in matching weights, and shows the source (e.g. "45% · from L0_Intro_City2026.pdf"). Findings it can't match to a Moodle entry (e.g. "Examination 70%") are listed on the module page and used when adding that exam. A small **edit** link stays as a backup; a weight I type is never overwritten.
- [ ] After the "Finding weights…" note clears, the app has set IN2013 quizzes to 2.5% (Low) and Coursework 1 to 45% (Medium), IN2015 Assessment 1/2 to 40%/60%, each showing its source file or page.
- Originally: weights entered manually in the module view.
- Priority from weight: **≤10% Low**, **over 10% to 50% Medium**, **over 50% High**.
- [ ] Entering 2.5% shows green Low; 30% shows yellow Medium; 70% shows red High.
- [ ] An assessment with no weight shows "⚠ Needs weight" in the month view instead of a priority.

### Excluding Non-Contributing Assessments
- Optional assessments that don't count toward the module are not included. In the module view, I mark them **Doesn't count**.
- Revised at the build checkpoint: the app also **detects optional assessments automatically** — no closing date (e.g. the DSA MCQs), "formative"/"practice"/"optional" in the name, or a description like "no mark". They're listed in the module view under **Optional — not included** with the reason and a **Counts** button to bring one back. "Doesn't count" items go to the same list, so they can be undone.
- [ ] Marking an assessment "Doesn't count" removes it from the month view, module counts, and Completed.
- [ ] The DSA quizzes (no closing date) and the Formative Activity appear only under "Optional — not included"; pressing "Counts" brings one back.

### EC and Extra-Time Versions
- EC and extra-time duplicates are hidden by default. The EC button shows them, each clearly labelled as EC/extra-time.
- [ ] By default, each coursework appears once (no EC/extra-time duplicate).
- [ ] Pressing the EC button shows the EC/extra-time versions labelled as such; pressing again hides them.

### Adding Exams
Added during `4-spec`: written exams are not on Moodle, so they'd otherwise be missing — and they're often the highest-weight items.
- Revised at final review ("make it find out all the exams and add it to the modules"): when a module's files mention an exam, the weight finder **adds it automatically** ("IN2002 Exam", 70%, source shown, tagged "found in your files"). If the file names a month ("exam in January") it shows in that month as **Date TBC**; otherwise it's listed under **Exams — date to confirm** on the dashboard. A **set date** link in the module adds the real date from the exam timetable. A module that already has an exam doesn't get another. **Vivas** are handled the same way, and so is **coursework not released on Moodle yet** (e.g. "IN2029 Coursework · 30%", "IN2013 Coursework 2 · 45%"), which is removed automatically once Moodle posts the real one. These appear under **Coming up — date to confirm**, below the monthly tables. The manual **Add exam** form was removed at final review (learner: "we dont need it anymore"); **set date** remains (e.g. "IN2002 Viva · 30%", with the file's hint "throughout week 10").
- In the module view, an **Add exam** form takes name, date, closing time, and weight.
- Added exams appear in the month view like any other assessment (type "Exam"), with priority from their weight.
- Moodle knows nothing about them, so they're completed by **manual tick** only.
- [ ] Adding "DSA Exam", a date in January, and 70% shows it in January's table as red High.
- [ ] Ticking it moves it to Completed and lowers the module's "left" count.

### Completion
- The app checks Moodle for completion; completed assessments move from the month view to **Completed**, and the module's "left" count goes down.
- Fallback: a manual tick if Moodle doesn't provide completion.
- [ ] After completing a quiz on Moodle, reloading the app shows it in Completed, not the month view.
- [ ] The module summary's "left" count drops by one.

## States and Boundaries
- **First use** — no weights yet: all current assessments appear in the month view with "⚠ Needs weight."
- **Offline / can't reach Moodle** — shows the message "Offline — assessments unable to update," with the last-loaded assessments still visible.
- **Empty month** — revised at final review: a month with nothing left to do (all completed, or nothing due) is not shown; if no month has anything, the dashboard says "Nothing coming up".
- **Persists between sessions** — weights, "Doesn't count" marks, manual ticks, and completed items.
- **Single user** — just me; no accounts or sharing.

## Product Decisions
- Assessments come from Moodle; I only add weights — keeps names/dates correct and the app focused on what Moodle lacks.
- Manual weights for now — reading slides automatically is too much for the PoC.
- "Needs weight" items stay visible in the month view with a ⚠ label — so a new real assessment is never missed.
- Optional/non-contributing assessments are excluded via "Doesn't count."
- Priority thresholds: ≤10% Low, ≤50% Medium, above High.
- Completed assessments move to a separate Completed area for review, not deleted.
- EC versions hidden behind a button — I don't apply for EC but want the option.
- Manually added exams (decided in `4-spec`) — exams are written and never appear on Moodle, but are the highest-weight items.
- An assessment belongs to the month of its closing date; offline shows last-loaded data; empty months say "No assessments" (confirmed at review).

## What We're Building
Dashboard with module summary and side-by-side month tables; Moodle loading for current modules; weight entry, "Doesn't count", and "Add exam" in the module view; colour-coded priority; ⚠ Needs weight label; EC show/hide button; completion detection from Moodle with manual-tick fallback; Completed area; offline message.

## Deferred From the POC
- (Reading weights automatically was deferred, then brought into the PoC during the build — see `Weights and Priority`.)

## Possible Later Enhancements
- An AI recommendations helper — discussed at final review; learner chose a free rule-based helper instead (see `Ask Crunch helper`). An AI version would need an API key, cost a little, and send the assessment list to the provider.
- A calendar view (raised at the build checkpoint; learner unsure of the details — "forget about it for now, I'll get back to you").

## Non-Goals
- Showing Moodle's full unfiltered list — that's the problem being replaced.
- Including optional/non-contributing assessments.
- Accounts, sharing, or use by other students.

## Open Questions
- Can my Moodle provide assessments and completion status to an outside app? — answer in `4-spec`.
