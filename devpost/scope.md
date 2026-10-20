---
doc: scope
status: approved
---

# Crunch

What matters when crunch time hits. A focused view of my upcoming university assessments, pulled from Moodle, with the noise stripped out and ranked by how much they're worth.

## The Unique Kernel
Moodle's timeline "slams everything together." This app shows only the assessments that actually apply to me — this year's modules, no EC/extra-time duplicates, no non-contributing practice quizzes — and **prioritises them by weight**, so when I'm short on time I know a 2.5% quiz can wait while a 70% exam can't.

## Who It's For
Me: a university student juggling several modules. Today I use the Moodle dashboard timeline, which mixes current and last year's modules, duplicate EC/extra-time entries, and practice quizzes, so "it can be difficult to know what you have coming up."

## The Core Loop
Open the app → see this month's real assessments (e.g. October), each with its type (quiz, exam, coursework, viva…), dates, and priority from its weight → do the work on Moodle → come back and see it marked completed. Flip between months to look ahead.

## Inspiration & Identity
Clear, focused, "easy to understand" — the opposite of the cluttered Moodle timeline. No visual references yet; `3-prd` fills this in.

## Why This Matters to the Learner
It solves a real daily frustration with tracking university deadlines. It's also a hands-on way to build skills working with AI coding agents — "AI is gonna be changing the technology landscape and I need to keep up."

## What "Working" Looks Like
Open the app and see October's assessments for current modules only, prioritised by weight. There's a quiz available 19–25 October; after I complete it on Moodle, the app checks Moodle and **marks it completed by itself** — that's the "oh, that's cool" moment. If my Moodle won't share completion status, a manual tick is an acceptable fallback.

## The POC Boundary
- Pull upcoming assessments from my Moodle.
- Show only current modules; hide last year's.
- Hide EC/extra-time duplicates by default, with an EC button to show them, clearly labelled, just in case.
- Exclude non-contributing assessments (e.g. practice/optional quizzes).
- Categorise each by type (quiz, exam, coursework, viva, etc.).
- Weights entered manually (e.g. DSA: viva 30%, exam 70%); priority derived from weight.
- Monthly view, one month at a time.
- Completion detected from Moodle; manual tick as fallback.

## Later
- Automatically reading weights from the module introductory slides (PDF/PowerPoint), instead of typing them in.

## Explicitly Cut
- Nothing else cut yet. Moodle's "show everything" approach is the problem this app replaces, so the full unfiltered list is deliberately not part of it.

## Open Risk
- Whether my university's Moodle lets an outside app read assessments and completion status. This will be checked in `4-spec`; the manual tick covers completion if not.
