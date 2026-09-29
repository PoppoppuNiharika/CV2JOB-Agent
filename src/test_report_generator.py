from pathlib import Path

import pytest

from parser import CVParser
from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from integrated_matcher import IntegratedMatcher
from gap_analyzer import GapAnalyzer
from improvement_planner import ImprovementPlanner
from report_generator import ReportGenerator


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CV_PATH = BASE_DIR / "test_cv.pdf"
JOB_PATH = BASE_DIR / "test_job_description.txt"


# =========================================================
# TEST FIXTURES
# =========================================================

@pytest.fixture
def generator():
    return ReportGenerator()


@pytest.fixture
def sample_integrated_result():
    return {
        "job_title": "DATA ANALYST INTERN",
        "basic_match": {
            "overall_match_percentage": 69.5,
        },
        "summary": {
            "total_requirements": 5,
            "confirmed_matches": 2,
            "evidence_matches": 1,
            "potential_matches": 1,
            "evidence_found": 3,
            "gaps": 1,
            "resolved_matches": 4,
            "coverage_percentage": 80.0,
        },
        "requirements": [
            {
                "requirement": "Python",
                "category": "Required Skill",
                "status": "Confirmed Match",
            },
            {
                "requirement": "SQL",
                "category": "Required Skill",
                "status": "Confirmed Match",
            },
            {
                "requirement": "Data Analysis",
                "category": "Required Skill",
                "status": "Evidence Match",
            },
            {
                "requirement": "Streamlit",
                "category": "Preferred Skill",
                "status": "Potential Match",
            },
            {
                "requirement": "Machine Learning",
                "category": "Preferred Skill",
                "status": "Gap",
            },
        ],
    }


@pytest.fixture
def sample_gap_analysis():
    return {
        "job_title": "DATA ANALYST INTERN",
        "gaps": [
            {
                "requirement": "Machine Learning",
                "category": "Preferred Skill",
                "priority": "Medium",
                "reason": "No evidence found.",
            }
        ],
        "evidence_improvements": [
            {
                "requirement": "Data Analysis",
                "category": "Required Skill",
                "priority": "Medium",
                "status": "Evidence Match",
            }
        ],
    }


@pytest.fixture
def sample_improvement_plan():
    return {
        "job_title": "DATA ANALYST INTERN",
        "action_plan": [
            {
                "requirement": "Machine Learning",
                "category": "Preferred Skill",
                "type": "Optional Skill Development",
                "priority": "Medium",
                "rationale": "Requirement is currently a gap.",
                "steps": [
                    "Learn the practical fundamentals.",
                    "Practice through a hands-on task.",
                    "Apply it to a relevant project.",
                    "Add it to the CV after genuine evidence exists.",
                ],
            },
            {
                "requirement": "Data Analysis",
                "category": "Required Skill",
                "type": "Evidence Improvement",
                "priority": "Medium",
                "rationale": "Existing evidence should be clearer.",
                "steps": [
                    "Review existing evidence.",
                    "Rewrite the CV bullet.",
                    "Add supported details.",
                    "Verify the revised bullet.",
                ],
            },
        ],
        "summary": {
            "total_actions": 2,
            "high_priority_actions": 0,
            "medium_priority_actions": 2,
            "low_priority_actions": 0,
            "skill_gap_actions": 1,
            "evidence_improvement_actions": 1,
        },
    }


# =========================================================
# BASIC REPORT TEST
# =========================================================

def test_generate_returns_expected_structure(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    report = generator.generate(
        sample_integrated_result,
        sample_gap_analysis,
        sample_improvement_plan,
    )

    assert isinstance(
        report,
        dict,
    )

    expected_keys = {
        "job_title",
        "overall_match",
        "coverage",
        "match_summary",
        "requirements",
        "gaps",
        "evidence_improvements",
        "improvement_plan",
        "improvement_summary",
    }

    assert expected_keys.issubset(
        report.keys()
    )


def test_report_values_are_preserved(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    report = generator.generate(
        sample_integrated_result,
        sample_gap_analysis,
        sample_improvement_plan,
    )

    assert report["job_title"] == (
        "DATA ANALYST INTERN"
    )

    assert report["overall_match"] == 69.5
    assert report["coverage"] == 80.0

    assert len(
        report["requirements"]
    ) == 5

    assert len(
        report["gaps"]
    ) == 1

    assert len(
        report["evidence_improvements"]
    ) == 1

    assert len(
        report["improvement_plan"]
    ) == 2


# =========================================================
# MATCH SUMMARY TESTS
# =========================================================

def test_match_summary_contains_new_status_counts(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    report = generator.generate(
        sample_integrated_result,
        sample_gap_analysis,
        sample_improvement_plan,
    )

    summary = report[
        "match_summary"
    ]

    assert summary[
        "total_requirements"
    ] == 5

    assert summary[
        "confirmed_matches"
    ] == 2

    assert summary[
        "evidence_matches"
    ] == 1

    assert summary[
        "potential_matches"
    ] == 1

    assert summary[
        "evidence_found"
    ] == 3

    assert summary[
        "gaps"
    ] == 1

    assert summary[
        "resolved_matches"
    ] == 4

    assert summary[
        "coverage_percentage"
    ] == 80.0


def test_missing_new_summary_fields_use_safe_defaults(
    generator,
):
    integrated_result = {
        "job_title": "Test Role",
        "basic_match": {
            "overall_match_percentage": 50.0,
        },
        "summary": {},
        "requirements": [],
    }

    report = generator.generate(
        integrated_result,
        {
            "gaps": [],
            "evidence_improvements": [],
        },
        {
            "action_plan": [],
            "summary": {},
        },
    )

    summary = report[
        "match_summary"
    ]

    assert summary[
        "evidence_matches"
    ] == 0

    assert summary[
        "potential_matches"
    ] == 0

    assert summary[
        "evidence_found"
    ] == 0

    assert summary[
        "resolved_matches"
    ] == 0


# =========================================================
# TOP-LEVEL VALIDATION
# =========================================================

def test_empty_integrated_result_raises(
    generator,
    sample_gap_analysis,
    sample_improvement_plan,
):
    with pytest.raises(
        ValueError
    ):
        generator.generate(
            {},
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_empty_gap_analysis_raises(
    generator,
    sample_integrated_result,
    sample_improvement_plan,
):
    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            {},
            sample_improvement_plan,
        )


def test_empty_improvement_plan_raises(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
):
    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            {},
        )


def test_integrated_result_must_be_dict(
    generator,
    sample_gap_analysis,
    sample_improvement_plan,
):
    with pytest.raises(
        TypeError
    ):
        generator.generate(
            [],
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_gap_analysis_must_be_dict(
    generator,
    sample_integrated_result,
    sample_improvement_plan,
):
    with pytest.raises(
        TypeError
    ):
        generator.generate(
            sample_integrated_result,
            [],
            sample_improvement_plan,
        )


def test_improvement_plan_must_be_dict(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
):
    with pytest.raises(
        TypeError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            [],
        )


# =========================================================
# FIELD VALIDATION
# =========================================================

def test_requirements_must_be_list(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    sample_integrated_result[
        "requirements"
    ] = {}

    with pytest.raises(
        TypeError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_invalid_requirement_status_raises(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    sample_integrated_result[
        "requirements"
    ][0]["status"] = "Invalid Status"

    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_invalid_gap_priority_raises(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    sample_gap_analysis[
        "gaps"
    ][0]["priority"] = "Urgent"

    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_invalid_action_priority_raises(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    sample_improvement_plan[
        "action_plan"
    ][0]["priority"] = "Urgent"

    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_negative_overall_match_raises(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    sample_integrated_result[
        "basic_match"
    ][
        "overall_match_percentage"
    ] = -1

    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            sample_improvement_plan,
        )


def test_over_100_coverage_raises(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    sample_integrated_result[
        "summary"
    ][
        "coverage_percentage"
    ] = 101

    with pytest.raises(
        ValueError
    ):
        generator.generate(
            sample_integrated_result,
            sample_gap_analysis,
            sample_improvement_plan,
        )


# =========================================================
# CONTENT PRESERVATION
# =========================================================

def test_gap_and_evidence_records_are_preserved(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    report = generator.generate(
        sample_integrated_result,
        sample_gap_analysis,
        sample_improvement_plan,
    )

    assert report["gaps"] == (
        sample_gap_analysis["gaps"]
    )

    assert report[
        "evidence_improvements"
    ] == (
        sample_gap_analysis[
            "evidence_improvements"
        ]
    )


def test_improvement_plan_is_preserved(
    generator,
    sample_integrated_result,
    sample_gap_analysis,
    sample_improvement_plan,
):
    report = generator.generate(
        sample_integrated_result,
        sample_gap_analysis,
        sample_improvement_plan,
    )

    assert report[
        "improvement_plan"
    ] == (
        sample_improvement_plan[
            "action_plan"
        ]
    )

    assert report[
        "improvement_summary"
    ] == (
        sample_improvement_plan[
            "summary"
        ]
    )


# =========================================================
# REAL PIPELINE TEST
# =========================================================

def build_real_pipeline():
    """
    Execute the actual current backend pipeline.
    """

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    cv_analyzer = CVAnalyzer()

    cv_profile = cv_analyzer.analyze(
        cv_text
    )

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    job_analyzer = JobAnalyzer()

    job_profile = job_analyzer.analyze(
        job_text
    )

    matcher = IntegratedMatcher()

    integrated_result = matcher.analyze(
        cv_profile,
        job_profile,
    )

    gap_analyzer = GapAnalyzer()

    gap_result = gap_analyzer.analyze(
        integrated_result
    )

    planner = ImprovementPlanner()

    improvement_result = planner.create_plan(
        gap_result
    )

    generator = ReportGenerator()

    report = generator.generate(
        integrated_result,
        gap_result,
        improvement_result,
    )

    return (
        integrated_result,
        gap_result,
        improvement_result,
        report,
    )


def test_real_pipeline_report(
    generator,
):
    (
        integrated_result,
        gap_result,
        improvement_result,
        report,
    ) = build_real_pipeline()

    assert isinstance(
        report,
        dict,
    )

    assert report["job_title"] == (
        "DATA ANALYST INTERN"
    )

    # These values come from the current pipeline and
    # are checked here to make sure the report layer
    # faithfully carries them forward.
    assert round(
        report["overall_match"],
        1,
    ) == 69.5

    assert round(
        report["coverage"],
        2,
    ) == 76.47

    summary = report[
        "match_summary"
    ]

    assert summary[
        "total_requirements"
    ] == 17

    assert summary[
        "confirmed_matches"
    ] == 11

    assert summary[
        "evidence_matches"
    ] == 2

    assert summary[
        "potential_matches"
    ] == 0

    assert summary[
        "evidence_found"
    ] == 13

    assert summary[
        "gaps"
    ] == 4

    assert summary[
        "resolved_matches"
    ] == 13

    assert round(
        summary["coverage_percentage"],
        2,
    ) == 76.47

    # Gap expectations from the current test CV/JD.
    gap_names = {
        gap["requirement"]
        for gap in report["gaps"]
    }

    assert "Scikit-learn" in gap_names
    assert "Machine Learning" in gap_names
    assert "Communication" in gap_names
    assert "Collaboration" in gap_names

    # Evidence-improvement expectations from the
    # current GapAnalyzer behavior.
    evidence_names = {
        item["requirement"]
        for item in report[
            "evidence_improvements"
        ]
    }

    assert "Data Analysis" in evidence_names
    assert "Data Visualization" in evidence_names

    # Phase 9 now creates one action per unique
    # gap/evidence requirement.
    assert len(
        report["improvement_plan"]
    ) == 6

    # Make sure the report did not mutate the
    # upstream outputs unexpectedly.
    assert (
        report["requirements"]
        == integrated_result["requirements"]
    )

    assert (
        report["improvement_plan"]
        == improvement_result["action_plan"]
    )

    assert (
        report["gaps"]
        == gap_result["gaps"]
    )


# =========================================================
# STANDALONE DISPLAY
# =========================================================

def main():
    print("=" * 70)
    print("REPORT GENERATOR TEST")
    print("=" * 70)

    (
        integrated_result,
        gap_result,
        improvement_result,
        report,
    ) = build_real_pipeline()

    print("\nCV2JOB ANALYSIS REPORT")
    print("-" * 70)

    print(
        f"Target Role: "
        f"{report['job_title']}"
    )

    print(
        f"Weighted Match: "
        f"{report['overall_match']:.2f}%"
    )

    print(
        f"Requirement Coverage: "
        f"{report['coverage']:.2f}%"
    )

    print("\nMATCH SUMMARY")
    print("-" * 70)

    summary = report[
        "match_summary"
    ]

    print(
        f"Total requirements: "
        f"{summary['total_requirements']}"
    )

    print(
        f"Confirmed matches: "
        f"{summary['confirmed_matches']}"
    )

    print(
        f"Evidence matches: "
        f"{summary['evidence_matches']}"
    )

    print(
        f"Potential matches: "
        f"{summary['potential_matches']}"
    )

    print(
        f"Evidence found: "
        f"{summary['evidence_found']}"
    )

    print(
        f"Gaps: "
        f"{summary['gaps']}"
    )

    print(
        f"Resolved matches: "
        f"{summary['resolved_matches']}"
    )

    print("\nGAPS")
    print("-" * 70)

    for gap in report[
        "gaps"
    ]:

        print(
            f"- {gap['requirement']} "
            f"({gap['category']}, "
            f"{gap['priority']} priority)"
        )

    print("\nEVIDENCE IMPROVEMENTS")
    print("-" * 70)

    for item in report[
        "evidence_improvements"
    ]:

        print(
            f"- {item['requirement']} "
            f"({item['category']}, "
            f"{item['priority']} priority)"
        )

    print("\nIMPROVEMENT PLAN")
    print("-" * 70)

    for index, action in enumerate(
        report["improvement_plan"],
        start=1,
    ):

        print(
            f"\n{index}. "
            f"{action['requirement']}"
        )

        print(
            f"   Category: "
            f"{action.get('category', '')}"
        )

        print(
            f"   Type: "
            f"{action['type']}"
        )

        print(
            f"   Priority: "
            f"{action['priority']}"
        )

        for step_number, step in enumerate(
            action["steps"],
            start=1,
        ):

            print(
                f"   {step_number}. "
                f"{step}"
            )

    print("\n" + "=" * 70)
    print("REPORT GENERATOR TEST: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()