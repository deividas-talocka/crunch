---
doc: prd
status: approved
---

# Assessment Tracker — Product Requirements

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
  - **Module summary** — one entry per current module: module name + number of assessments left.
  - **Month view** — month name as a heading with a table of its assessments beneath; the next month sits beside it, and so on.
  - **EC button** — shows/hides EC and extra-time versions.
- **Module view** — opened by clicking a module: lists that module's Moodle assessments, where I enter weights or mark "Doesn't count."
- **Completed** — a separate place holding all completed assessments for review.

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
- [ ] Every assessment row shows all seven fields plus its type.
- [ ] An assessment appears under the month of its closing date.

### Weights and Priority
- Weights are entered manually in the module view (`scope.md > Later`: auto-reading slides is deferred).
- Priority from weight: **≤10% Low**, **over 10% to 50% Medium**, **over 50% High**.
- [ ] Entering 2.5% shows green Low; 30% shows yellow Medium; 70% shows red High.
- [ ] An assessment with no weight shows "⚠ Needs weight" in the month view instead of a priority.

### Excluding Non-Contributing Assessments
- Optional assessments that don't count toward the module are not included. In the module view, I mark them **Doesn't count**.
- [ ] Marking an assessment "Doesn't count" removes it from the month view, module counts, and Completed.

### EC and Extra-Time Versions
- EC and extra-time duplicates are hidden by default. The EC button shows them, each clearly labelled as EC/extra-time.
- [ ] By default, each coursework appears once (no EC/extra-time duplicate).
- [ ] Pressing the EC button shows the EC/extra-time versions labelled as such; pressing again hides them.

### Adding Exams
Added during `4-spec`: written exams are not on Moodle, so they'd otherwise be missing — and they're often the highest-weight items.
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
- **Empty month** — shows the month with "No assessments."
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
- Reading weights automatically from module introductory slides — hard to do reliably across different lecturers' formats.

## Possible Later Enhancements
- Auto-read weights from slides (see above).

## Non-Goals
- Showing Moodle's full unfiltered list — that's the problem being replaced.
- Including optional/non-contributing assessments.
- Accounts, sharing, or use by other students.

## Open Questions
- Can my Moodle provide assessments and completion status to an outside app? — answer in `4-spec`.
