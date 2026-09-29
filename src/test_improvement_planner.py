from pathlib import Path

import pytest

from parser import CVParser
from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from integrated_matcher import IntegratedMatcher
from gap_analyzer import GapAnalyzer
from improvement_planner import ImprovementPlanner


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
def planner():
    return ImprovementPlanner()


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
            },
            {
                "requirement": "Communication",
                "category": "Soft Skill",
                "priority": "Medium",
                "reason": "No evidence found.",
            },
            {
                "requirement": "SQL",
                "category": "Required Skill",
                "priority": "High",
                "reason": "No evidence found.",
            },
        ],
        "evidence_improvements": [
            {
                "requirement": "Data Analysis",
                "category": "Required Skill",
                "priority": "Medium",
                "status": "Evidence Match",
            },
            {
                "requirement": "Data Visualization",
                "category": "Required Skill",
                "priority": "Medium",
                "status": "Evidence Match",
            },
        ],
    }


# =========================================================
# BASIC STRUCTURE TESTS
# =========================================================

def test_create_plan_returns_expected_structure(
    planner,
    sample_gap_analysis,
):
    result = planner.create_plan(
        sample_gap_analysis
    )

    assert isinstance(
        result,
        dict,
    )

    assert result["job_title"] == (
        "DATA ANALYST INTERN"
    )

    assert isinstance(
        result["action_plan"],
        list,
    )

    assert isinstance(
        result["summary"],
        dict,
    )


def test_empty_action_plan_is_valid(
    planner,
):
    result = planner.create_plan(
        {
            "job_title": "Data Analyst Intern",
            "gaps": [],
            "evidence_improvements": [],
        }
    )

    assert result["action_plan"] == []

    assert result["summary"]["total_actions"] == 0
    assert result["summary"]["high_priority_actions"] == 0
    assert result["summary"]["medium_priority_actions"] == 0
    assert result["summary"]["low_priority_actions"] == 0


# =========================================================
# VALIDATION TESTS
# =========================================================

def test_non_dict_input_raises(
    planner,
):
    with pytest.raises(TypeError):
        planner.create_plan(
            []
        )


def test_empty_dict_raises(
    planner,
):
    with pytest.raises(ValueError):
        planner.create_plan(
            {}
        )


def test_gaps_must_be_list(
    planner,
):
    with pytest.raises(TypeError):
        planner.create_plan(
            {
                "gaps": {},
                "evidence_improvements": [],
            }
        )


def test_evidence_improvements_must_be_list(
    planner,
):
    with pytest.raises(TypeError):
        planner.create_plan(
            {
                "gaps": [],
                "evidence_improvements": {},
            }
        )


def test_gap_item_must_be_dict(
    planner,
):
    with pytest.raises(TypeError):
        planner.create_plan(
            {
                "gaps": [
                    "Machine Learning"
                ],
                "evidence_improvements": [],
            }
        )


def test_missing_gap_requirement_raises(
    planner,
):
    with pytest.raises(ValueError):
        planner.create_plan(
            {
                "gaps": [
                    {
                        "category": "Required Skill",
                        "priority": "High",
                    }
                ],
                "evidence_improvements": [],
            }
        )


def test_invalid_priority_raises(
    planner,
):
    with pytest.raises(ValueError):
        planner.create_plan(
            {
                "gaps": [
                    {
                        "requirement": "Python",
                        "category": "Required Skill",
                        "priority": "Urgent",
                    }
                ],
                "evidence_improvements": [],
            }
        )


# =========================================================
# GAP ACTION TESTS
# =========================================================

def test_required_skill_action(
    planner,
):
    result = planner.create_plan(
        {
            "job_title": "Data Analyst",
            "gaps": [
                {
                    "requirement": "SQL",
                    "category": "Required Skill",
                    "priority": "High",
                }
            ],
            "evidence_improvements": [],
        }
    )

    action = result["action_plan"][0]

    assert action["requirement"] == "SQL"
    assert action["category"] == "Required Skill"
    assert action["type"] == "Skill Development"
    assert action["priority"] == "High"

    assert len(
        action["steps"]
    ) == 4

    assert "SQL" in action["steps"][0]
    assert "SQL" in action["steps"][1]
    assert "SQL" in action["steps"][2]


def test_preferred_skill_action(
    planner,
):
    result = planner.create_plan(
        {
            "job_title": "Data Analyst",
            "gaps": [
                {
                    "requirement": "Scikit-learn",
                    "category": "Preferred Skill",
                    "priority": "Medium",
                }
            ],
            "evidence_improvements": [],
        }
    )

    action = result["action_plan"][0]

    assert action["requirement"] == "Scikit-learn"
    assert action["category"] == "Preferred Skill"
    assert action["type"] == (
        "Optional Skill Development"
    )

    assert len(
        action["steps"]
    ) == 4

    assert "Scikit-learn" in action["steps"][0]


def test_soft_skill_action(
    planner,
):
    result = planner.create_plan(
        {
            "job_title": "Data Analyst",
            "gaps": [
                {
                    "requirement": "Communication",
                    "category": "Soft Skill",
                    "priority": "Medium",
                }
            ],
            "evidence_improvements": [],
        }
    )

    action = result["action_plan"][0]

    assert action["requirement"] == "Communication"
    assert action["category"] == "Soft Skill"
    assert action["type"] == "Evidence Development"

    assert len(
        action["steps"]
    ) == 3

    assert "Communication" in action["steps"][0]


def test_other_category_action(
    planner,
):
    result = planner.create_plan(
        {
            "job_title": "Analyst",
            "gaps": [
                {
                    "requirement": "Related Field",
                    "category": "Other",
                    "priority": "Low",
                }
            ],
            "evidence_improvements": [],
        }
    )

    action = result["action_plan"][0]

    assert action["type"] == (
        "Requirement Review"
    )

    assert len(
        action["steps"]
    ) == 3


# =========================================================
# EVIDENCE IMPROVEMENT TESTS
# =========================================================

def test_evidence_improvement_action(
    planner,
):
    result = planner.create_plan(
        {
            "job_title": "Data Analyst",
            "gaps": [],
            "evidence_improvements": [
                {
                    "requirement": "Data Analysis",
                    "category": "Required Skill",
                    "priority": "Medium",
                }
            ],
        }
    )

    action = result["action_plan"][0]

    assert action["requirement"] == (
        "Data Analysis"
    )

    assert action["category"] == (
        "Required Skill"
    )

    assert action["type"] == (
        "Evidence Improvement"
    )

    assert action["priority"] == "Medium"

    assert len(
        action["steps"]
    ) == 4

    assert "Data Analysis" in (
        action["steps"][0]
    )


def test_evidence_improvement_does_not_assume_learning_gap(
    planner,
):
    result = planner.create_plan(
        {
            "gaps": [],
            "evidence_improvements": [
                {
                    "requirement": "Power BI",
                    "category": "Required Skill",
                    "priority": "Medium",
                }
            ],
        }
    )

    action = result["action_plan"][0]

    assert action["type"] == (
        "Evidence Improvement"
    )

    assert "learn" not in (
        action["rationale"].lower()
    )


# =========================================================
# DUPLICATE HANDLING
# =========================================================

def test_duplicate_gaps_are_removed(
    planner,
):
    result = planner.create_plan(
        {
            "gaps": [
                {
                    "requirement": "Python",
                    "category": "Required Skill",
                    "priority": "High",
                },
                {
                    "requirement": " python ",
                    "category": "Required Skill",
                    "priority": "High",
                },
            ],
            "evidence_improvements": [],
        }
    )

    requirements = [
        action["requirement"]
        for action in result["action_plan"]
    ]

    assert requirements == [
        "Python"
    ]


def test_gap_takes_precedence_over_evidence_improvement(
    planner,
):
    result = planner.create_plan(
        {
            "gaps": [
                {
                    "requirement": "Machine Learning",
                    "category": "Preferred Skill",
                    "priority": "Medium",
                }
            ],
            "evidence_improvements": [
                {
                    "requirement": "machine learning",
                    "category": "Preferred Skill",
                    "priority": "Low",
                }
            ],
        }
    )

    assert len(
        result["action_plan"]
    ) == 1

    action = result["action_plan"][0]

    assert action["requirement"] == (
        "Machine Learning"
    )

    assert action["type"] == (
        "Optional Skill Development"
    )


# =========================================================
# PRIORITY AND SUMMARY TESTS
# =========================================================

def test_actions_are_sorted_by_priority(
    planner,
):
    result = planner.create_plan(
        {
            "gaps": [
                {
                    "requirement": "Low Skill",
                    "category": "Preferred Skill",
                    "priority": "Low",
                },
                {
                    "requirement": "High Skill",
                    "category": "Required Skill",
                    "priority": "High",
                },
                {
                    "requirement": "Medium Skill",
                    "category": "Soft Skill",
                    "priority": "Medium",
                },
            ],
            "evidence_improvements": [],
        }
    )

    requirements = [
        action["requirement"]
        for action in result["action_plan"]
    ]

    assert requirements == [
        "High Skill",
        "Medium Skill",
        "Low Skill",
    ]


def test_summary_counts_are_consistent(
    planner,
    sample_gap_analysis,
):
    result = planner.create_plan(
        sample_gap_analysis
    )

    summary = result["summary"]

    assert summary["total_actions"] == 5

    assert summary["high_priority_actions"] == 1
    assert summary["medium_priority_actions"] == 4
    assert summary["low_priority_actions"] == 0

    assert summary["skill_gap_actions"] == 3
    assert summary["evidence_improvement_actions"] == 2

    assert (
        summary["high_priority_actions"]
        + summary["medium_priority_actions"]
        + summary["low_priority_actions"]
        == summary["total_actions"]
    )


def test_missing_priority_defaults_to_low(
    planner,
):
    result = planner.create_plan(
        {
            "gaps": [
                {
                    "requirement": "Python",
                    "category": "Required Skill",
                }
            ],
            "evidence_improvements": [],
        }
    )

    action = result["action_plan"][0]

    assert action["priority"] == "Low"


def test_whitespace_is_normalized(
    planner,
):
    result = planner.create_plan(
        {
            "gaps": [
                {
                    "requirement": "   Machine    Learning   ",
                    "category": "Preferred Skill",
                    "priority": "Medium",
                }
            ],
            "evidence_improvements": [],
        }
    )

    action = result["action_plan"][0]

    assert action["requirement"] == (
        "Machine Learning"
    )


# =========================================================
# REAL PIPELINE COMPATIBILITY TEST
# =========================================================

def build_real_gap_analysis():
    """
    Run the real current backend pipeline once and return
    the GapAnalyzer result.

    This checks that the ImprovementPlanner accepts the
    actual output produced by the project.
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

    return gap_analyzer.analyze(
        integrated_result
    )


def test_real_pipeline_compatibility(
    planner,
):
    gap_result = build_real_gap_analysis()

    plan = planner.create_plan(
        gap_result
    )

    assert isinstance(
        plan,
        dict,
    )

    assert "action_plan" in plan
    assert "summary" in plan

    requirements = {
        action["requirement"]
        for action in plan["action_plan"]
    }

    assert "Scikit-learn" in requirements
    assert "Machine Learning" in requirements

    # The current real pipeline also identifies evidence
    # improvements for Data Analysis and Data Visualization.
    assert (
        "Data Analysis"
        in requirements
    )

    assert (
        "Data Visualization"
        in requirements
    )


# =========================================================
# STANDALONE DISPLAY
# =========================================================

def main():
    print("=" * 70)
    print("IMPROVEMENT PLANNER TEST")
    print("=" * 70)

    gap_result = build_real_gap_analysis()

    planner = ImprovementPlanner()

    plan = planner.create_plan(
        gap_result
    )

    print("\nJOB TITLE")
    print("-" * 70)
    print(
        plan["job_title"]
    )

    print("\nPLAN SUMMARY")
    print("-" * 70)

    summary = plan["summary"]

    print(
        f"Total actions: "
        f"{summary['total_actions']}"
    )

    print(
        f"High priority: "
        f"{summary['high_priority_actions']}"
    )

    print(
        f"Medium priority: "
        f"{summary['medium_priority_actions']}"
    )

    print(
        f"Low priority: "
        f"{summary['low_priority_actions']}"
    )

    print(
        f"Skill-gap actions: "
        f"{summary['skill_gap_actions']}"
    )

    print(
        f"Evidence-improvement actions: "
        f"{summary['evidence_improvement_actions']}"
    )

    print("\nTARGETED IMPROVEMENT PLAN")
    print("-" * 70)

    for index, action in enumerate(
        plan["action_plan"],
        start=1,
    ):

        print(
            f"\n{index}. "
            f"{action['requirement']}"
        )

        print(
            f"   Category: "
            f"{action['category']}"
        )

        print(
            f"   Type: "
            f"{action['type']}"
        )

        print(
            f"   Priority: "
            f"{action['priority']}"
        )

        print(
            f"   Rationale: "
            f"{action['rationale']}"
        )

        print("   Steps:")

        for step_number, step in enumerate(
            action["steps"],
            start=1,
        ):

            print(
                f"      {step_number}. "
                f"{step}"
            )

    print("\n" + "=" * 70)
    print("IMPROVEMENT PLANNER TEST: SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    main()