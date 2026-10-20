"""Uses real sentences found in the learner's module pages and PDFs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import weight_finder as wf  # noqa: E402

IN2013_INTRO = """The pass mark for the module is 40%.
• CW 1 (Analysis) is worth 45% of module mark.
• CW2 (Design) is worth 45% of the module mark.
• MCQ results (4 best out of the 5 offered) are together worth 10% of module mark (i.e., each
MCQ quiz taken into account is worth 2.5% of the module mark)."""
IN2013_LABEL = "Quizzes There will be 5 MCQ quizzes in this module. The quizzes are collectively worth 10% of the module mark"
IN2015_LABEL = ("Assessment 1: Professional Presentation (40%) Assessment 2: Summary of Professional "
                "Development (60%) Further details below")
IN2029_SCHEDULE = "Assessment\nCoursework\n30%\nExamination\n70%"
IN2002_OVERVIEW = """Summative assessments:
▪ Oral coursework (viva) throughout week 10 based on lectures and
tutorials (30% of module mark)
▪ Written open “books” exam in January (70% of module mark)
▪ 161 passed 1st attempt (71.6%; 10% had EC)
5. 91% passed the module, out of these 2.2% progressed by compensating this module."""
QUIZ_EXTRA_TIME = "You are given 30 min to complete the quiz as you have a confirmed condition and are entitled to 50% longer time"


def summary(findings):
    return [(f["kind"], f["number"], f["percent"], f["combined"]) for f in findings]


def test_reads_real_lines_and_skips_noise():
    assert summary(wf.find_weights(IN2013_INTRO, "L0.pdf")) == [
        ("coursework", 1, 45, False), ("coursework", 2, 45, False),
        ("quiz", None, 10, True), ("quiz", None, 2.5, False),
    ]
    assert summary(wf.find_weights(IN2015_LABEL, "Moodle page")) == [
        ("assessment", 1, 40, False), ("assessment", 2, 60, False)]
    assert summary(wf.find_weights(IN2029_SCHEDULE, "schedule.pdf")) == [
        ("coursework", None, 30, False), ("exam", None, 70, False)]
    assert summary(wf.find_weights(IN2002_OVERVIEW, "DSA0.pdf")) == [
        ("viva", None, 30, False), ("exam", None, 70, False)]
    assert wf.find_weights(QUIZ_EXTRA_TIME, "Moodle page") == []


def test_matches_findings_to_moodle_assessments():
    findings = wf.find_weights(IN2013_INTRO, "L0.pdf") + wf.find_weights(IN2013_LABEL, "Moodle page")
    items = [
        {"id": "quiz-1", "name": "Quiz 1 on Lecture 1 and 2", "kind": "quiz", "ec": False},
        {"id": "quiz-2", "name": "Quiz 1 on Lecture 1 and 2 (Extra Time, SSP)", "kind": "quiz", "ec": True},
        {"id": "quiz-3", "name": "Quiz 2 on Lecture 3 and 4", "kind": "quiz", "ec": False},
        {"id": "assign-1", "name": "Coursework 1 (Analysis) Submission Area (2026 - 27)", "kind": "assign", "ec": False},
        {"id": "assign-2", "name": "CW1 (Analysis) submission area (2026-27) - Extenuating Circumstances", "kind": "assign", "ec": True},
    ]
    chosen, unmatched = wf.match(findings, items)
    assert {k: v["percent"] for k, v in chosen.items()} == {
        "quiz-1": 2.5, "quiz-2": 2.5, "quiz-3": 2.5, "assign-1": 45, "assign-2": 45}
    assert chosen["assign-1"]["source"] == "L0.pdf"
    assert [(f["kind"], f["number"], f["percent"]) for f in unmatched] == [("coursework", 2, 45)]


def test_assessment_numbers_and_unmatched_exam():
    items = [
        {"id": "assign-1", "name": "Assessment 1 submission area", "kind": "assign", "ec": False},
        {"id": "assign-2", "name": "Assessment 2 submission area", "kind": "assign", "ec": False},
    ]
    chosen, _ = wf.match(wf.find_weights(IN2015_LABEL, "Moodle page"), items)
    assert {k: v["percent"] for k, v in chosen.items()} == {"assign-1": 40, "assign-2": 60}

    chosen, unmatched = wf.match(wf.find_weights(IN2029_SCHEDULE, "schedule.pdf"), [])
    assert chosen == {} and [f["kind"] for f in unmatched] == ["coursework", "exam"]


def test_manual_exam_gets_exam_weight():
    items = [{"id": "exam-1", "name": "DSA Exam", "kind": "exam", "ec": False}]
    chosen, _ = wf.match(wf.find_weights(IN2002_OVERVIEW, "DSA0.pdf"), items)
    assert chosen["exam-1"]["percent"] == 70


def test_exams_and_vivas_found_in_files_are_added_once():
    _, unmatched = wf.match(wf.find_weights(IN2002_OVERVIEW, "DSA0.pdf"), [])
    added = wf.exams_to_add(7, "IN2002", unmatched, [])
    assert [(e["name"], e["weight"], e["month"], e["weight_source"]) for e in added] == [
        ("IN2002 Exam", 70, 1, "DSA0.pdf"), ("IN2002 Viva", 30, None, "DSA0.pdf")]
    assert "week 10" in added[1]["hint"]
    # already has an exam (added by me, no found_kind) -> only the viva is added
    assert [e["name"] for e in wf.exams_to_add(7, "IN2002", unmatched, [{"course_id": 7}])] == ["IN2002 Viva"]
    _, unmatched = wf.match(wf.find_weights(IN2029_SCHEDULE, "schedule.pdf"), [])
    assert [(e["name"], e["month"]) for e in wf.exams_to_add(8, "IN2029", unmatched, [])] == [("IN2029 Exam", None)]


def test_rescan_rules():
    now = 1_000_000
    weighted = {"id": 1, "items": [{"weight": 45, "ec": False}]}
    unweighted = {"id": 2, "items": [{"weight": None, "ec": False}]}
    v = wf.SCAN_VERSION
    notes = {"scans": {"1": {"at": now - 10, "version": v}, "2": {"at": now - 10, "version": v}}}
    assert wf.courses_needing_scan([weighted, unweighted], notes, now) == []
    later = now + wf.RESCAN_AFTER + 1
    assert wf.courses_needing_scan([weighted, unweighted], notes, later) == [unweighted]
    assert wf.courses_needing_scan([weighted], {}, now) == [weighted]
