from pathlib import Path

import pytest

from parser import CVParser
from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from integrated_matcher import IntegratedMatcher
from gap_analyzer import GapAnalyzer


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CV_PATH = BASE_DIR / "test_cv.pdf"
JOB_PATH = BASE_DIR / "test_job_description.txt"


# =========================================================
# TEST HELPERS
# =========================================================

def make_requirement(
    requirement,
    category,
    status,
    evidence=None,
    semantic_score=0.0,
):
    """
    Create a minimal integrated requirement record.
    """

    return {
        "requirement": requirement,
        "category": category,
        "status": status,
        "confidence": "Medium",
        "basic_match": (
            "Exact Match"
            if status == "Confirmed Match"
            else "Not Exact Match"
        ),
        "semantic_score": semantic_score,
        "semantic_level": "Related Evidence",
        "evidence": evidence or [],
        "best_semantic_evidence": "",
    }


def make_integrated_result(
    requirements,
):
    """
    Create a minimal integrated result.
    """

    return {
        "job_title": "TEST JOB",
        "requirements": requirements,
        "summary": {},
        "basic_match": {
            "required_skills": {
                "matched": [],
                "missing": [],
            },
            "preferred_skills": {
                "matched": [],
                "missing": [],
            },
            "soft_skills": {
                "matched": [],
                "missing": [],
            },
        },
        "evidence_mapping": {},
    }


# =========================================================
# EMPTY INPUT
# =========================================================

def test_empty_result_rejected():

    analyzer = GapAnalyzer()

    with pytest.raises(
        ValueError
    ):

        analyzer.analyze(
            {}
        )


# =========================================================
# INVALID INPUT TYPE
# =========================================================

def test_non_dictionary_result_rejected():

    analyzer = GapAnalyzer()

    with pytest.raises(
        TypeError
    ):

        analyzer.analyze(
            []
        )


# =========================================================
# CONFIRMED MATCH
# =========================================================

def test_confirmed_match_creates_no_action():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="Python",
                    category="Required Skill",
                    status="Confirmed Match",
                    evidence=[
                        {
                            "source": "Technical Skills",
                            "text": "Python",
                        }
                    ],
                )
            ]
        )
    )

    assert result["gaps"] == []

    assert (
        result["evidence_improvements"]
        == []
    )

    assert (
        result["summary"]["total_gaps"]
        == 0
    )

    assert (
        result["summary"]["evidence_improvements"]
        == 0
    )


# =========================================================
# EVIDENCE MATCH
# =========================================================

def test_evidence_match_creates_improvement():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="Data Visualization",
                    category="Required Skill",
                    status="Evidence Match",
                    evidence=[
                        {
                            "source": "Project",
                            "text": (
                                "Created Matplotlib "
                                "visualizations."
                            ),
                        }
                    ],
                    semantic_score=0.65,
                )
            ]
        )
    )

    assert result["gaps"] == []

    assert (
        len(
            result["evidence_improvements"]
        )
        == 1
    )

    improvement = (
        result["evidence_improvements"][0]
    )

    assert (
        improvement["requirement"]
        == "Data Visualization"
    )

    assert (
        improvement["type"]
        == "Strengthen Evidence"
    )

    assert (
        improvement["priority"]
        == "Medium"
    )


# =========================================================
# EVIDENCE FOUND
# =========================================================

def test_evidence_found_is_not_silently_ignored():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="Data Analysis",
                    category="Required Skill",
                    status="Evidence Found",
                    evidence=[
                        {
                            "source": "Project",
                            "text": (
                                "Analyzed datasets."
                            ),
                        }
                    ],
                    semantic_score=0.20,
                )
            ]
        )
    )

    assert result["gaps"] == []

    assert (
        len(
            result["evidence_improvements"]
        )
        == 1
    )

    improvement = (
        result["evidence_improvements"][0]
    )

    assert (
        improvement["requirement"]
        == "Data Analysis"
    )

    assert (
        improvement["type"]
        == "Strengthen Evidence"
    )

    assert (
        improvement["priority"]
        == "Medium"
    )


# =========================================================
# POTENTIAL MATCH
# =========================================================

def test_potential_match_creates_add_evidence_action():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="SQL",
                    category="Required Skill",
                    status="Potential Match",
                    semantic_score=0.85,
                )
            ]
        )
    )

    assert result["gaps"] == []

    assert (
        len(
            result["evidence_improvements"]
        )
        == 1
    )

    improvement = (
        result["evidence_improvements"][0]
    )

    assert (
        improvement["requirement"]
        == "SQL"
    )

    assert (
        improvement["type"]
        == "Add Evidence"
    )

    assert (
        improvement["priority"]
        == "Medium"
    )


# =========================================================
# REQUIRED SKILL GAP
# =========================================================

def test_required_skill_gap_is_high_priority():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="Machine Learning",
                    category="Required Skill",
                    status="Gap",
                    semantic_score=0.20,
                )
            ]
        )
    )

    assert (
        len(
            result["gaps"]
        )
        == 1
    )

    gap = result["gaps"][0]

    assert (
        gap["requirement"]
        == "Machine Learning"
    )

    assert (
        gap["category"]
        == "Required Skill"
    )

    assert (
        gap["priority"]
        == "High"
    )

    assert (
        "Machine Learning"
        in gap["suggested_action"]
    )


# =========================================================
# PREFERRED SKILL GAP
# =========================================================

def test_preferred_skill_gap_is_medium_priority():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="Scikit-learn",
                    category="Preferred Skill",
                    status="Gap",
                    semantic_score=0.20,
                )
            ]
        )
    )

    assert (
        len(
            result["gaps"]
        )
        == 1
    )

    gap = result["gaps"][0]

    assert (
        gap["priority"]
        == "Medium"
    )


# =========================================================
# SOFT SKILL GAP
# =========================================================

def test_soft_skill_gap_is_medium_priority():

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        make_integrated_result(
            [
                make_requirement(
                    requirement="Communication",
                    category="Soft Skill",
                    status="Gap",
                    semantic_score=0.20,
                )
            ]
        )
    )

    assert (
        len(
            result["gaps"]
        )
        == 1
    )

    gap = result["gaps"][0]

    assert (
        gap["category"]
        == "Soft Skill"
    )

    assert (
        gap["priority"]
        == "Medium"
    )


# =========================================================
# CATEGORY FROM INTEGRATED REQUIREMENT
# =========================================================

def test_direct_category_is_preferred():

    analyzer = GapAnalyzer()

    integrated = make_integrated_result(
        [
            make_requirement(
                requirement="SQL",
                category="Required Skill",
                status="Gap",
            )
        ]
    )

    # Deliberately make basic_match inconsistent.
    integrated["basic_match"][
        "preferred_skills"
    ]["missing"] = [
        "SQL"
    ]

    result = analyzer.analyze(
        integrated
    )

    assert (
        result["gaps"][0]["category"]
        == "Required Skill"
    )


# =========================================================
# CATEGORY FALLBACK
# =========================================================

def test_basic_match_category_fallback():

    analyzer = GapAnalyzer()

    requirement = make_requirement(
        requirement="SQL",
        category="",
        status="Gap",
    )

    integrated = make_integrated_result(
        [
            requirement
        ]
    )

    integrated["basic_match"][
        "required_skills"
    ]["missing"] = [
        "SQL"
    ]

    result = analyzer.analyze(
        integrated
    )

    assert (
        result["gaps"][0]["category"]
        == "Required Skill"
    )


# =========================================================
# GAP REASON
# =========================================================

def test_gap_reason_for_low_semantic_score():

    analyzer = GapAnalyzer()

    requirement = make_requirement(
        requirement="Machine Learning",
        category="Preferred Skill",
        status="Gap",
        semantic_score=0.20,
    )

    result = analyzer.analyze(
        make_integrated_result(
            [requirement]
        )
    )

    assert (
        result["gaps"][0]["reason"]
        ==
        "No explicit CV evidence was found "
        "and semantic similarity is low."
    )


def test_gap_reason_when_related_semantics_exist():

    analyzer = GapAnalyzer()

    requirement = make_requirement(
        requirement="Machine Learning",
        category="Preferred Skill",
        status="Gap",
        semantic_score=0.65,
    )

    result = analyzer.analyze(
        make_integrated_result(
            [requirement]
        )
    )

    assert (
        result["gaps"][0]["reason"]
        ==
        "No explicit CV evidence was found."
    )


# =========================================================
# DUPLICATES
# =========================================================

def test_duplicate_requirements_are_deduplicated():

    analyzer = GapAnalyzer()

    requirements = [
        make_requirement(
            requirement="Python",
            category="Required Skill",
            status="Gap",
        ),
        make_requirement(
            requirement="Python",
            category="Required Skill",
            status="Gap",
        ),
    ]

    result = analyzer.analyze(
        make_integrated_result(
            requirements
        )
    )

    assert (
        len(
            result["gaps"]
        )
        == 1
    )


# =========================================================
# UNKNOWN STATUS
# =========================================================

def test_unknown_status_is_rejected():

    analyzer = GapAnalyzer()

    requirement = make_requirement(
        requirement="Python",
        category="Required Skill",
        status="Something Invalid",
    )

    with pytest.raises(
        ValueError
    ):

        analyzer.analyze(
            make_integrated_result(
                [requirement]
            )
        )


# =========================================================
# SUMMARY CONSISTENCY
# =========================================================

def test_summary_counts_are_consistent():

    analyzer = GapAnalyzer()

    requirements = [
        make_requirement(
            "Python",
            "Required Skill",
            "Confirmed Match",
        ),
        make_requirement(
            "Data Analysis",
            "Required Skill",
            "Evidence Match",
            evidence=[
                {
                    "source": "Project",
                    "text": "Analyzed data.",
                }
            ],
            semantic_score=0.65,
        ),
        make_requirement(
            "SQL",
            "Required Skill",
            "Potential Match",
            semantic_score=0.85,
        ),
        make_requirement(
            "Machine Learning",
            "Preferred Skill",
            "Gap",
            semantic_score=0.20,
        ),
        make_requirement(
            "Communication",
            "Soft Skill",
            "Gap",
            semantic_score=0.20,
        ),
    ]

    result = analyzer.analyze(
        make_integrated_result(
            requirements
        )
    )

    summary = result[
        "summary"
    ]

    assert (
        summary["total_gaps"]
        == 2
    )

    assert (
        summary["high_priority_gaps"]
        == 0
    )

    assert (
        summary["medium_priority_gaps"]
        == 2
    )

    assert (
        summary["low_priority_gaps"]
        == 0
    )

    assert (
        summary["evidence_improvements"]
        == 2
    )


# =========================================================
# REAL CV/JD INTEGRATION SMOKE TEST
# =========================================================

@pytest.fixture(scope="module")
def real_integrated_result():

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    links = parser.extract_links(
        CV_PATH
    )

    cv_analyzer = CVAnalyzer()

    cv_profile = cv_analyzer.analyze(
        cv_text,
        links=links,
    )

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    job_analyzer = JobAnalyzer()

    job_profile = job_analyzer.analyze(
        job_text
    )

    matcher = IntegratedMatcher()

    return matcher.analyze(
        cv_profile,
        job_profile,
    )


def test_real_gap_analysis(
    real_integrated_result,
):

    analyzer = GapAnalyzer()

    result = analyzer.analyze(
        real_integrated_result
    )

    assert isinstance(
        result,
        dict,
    )

    assert set(
        result.keys()
    ) == {
        "job_title",
        "gaps",
        "evidence_improvements",
        "summary",
    }

    assert (
        result["job_title"]
        == "DATA ANALYST INTERN"
    )

    # Current fixture contains four actual gaps.
    assert (
        result["summary"]["total_gaps"]
        == 4
    )

    gap_names = [
        gap["requirement"]
        for gap in result["gaps"]
    ]

    assert (
        "Scikit-learn"
        in gap_names
    )

    assert (
        "Machine Learning"
        in gap_names
    )

    assert (
        "Communication"
        in gap_names
    )

    assert (
        "Collaboration"
        in gap_names
    )

    improvement_names = [
        item["requirement"]
        for item in result[
            "evidence_improvements"
        ]
    ]

    assert (
        "Data Analysis"
        in improvement_names
    )

    assert (
        "Data Visualization"
        in improvement_names
    )


# =========================================================
# STANDALONE RUNNER
# =========================================================

def main():

    print(
        "=" * 70
    )

    print(
        "GAP ANALYSIS TEST"
    )

    print(
        "=" * 70
    )

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    links = parser.extract_links(
        CV_PATH
    )

    cv_analyzer = CVAnalyzer()

    cv_profile = cv_analyzer.analyze(
        cv_text,
        links=links,
    )

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    job_analyzer = JobAnalyzer()

    job_profile = job_analyzer.analyze(
        job_text
    )

    print(
        "\nLoading integrated matching engine..."
    )

    matcher = IntegratedMatcher()

    integrated_result = matcher.analyze(
        cv_profile,
        job_profile,
    )

    analyzer = GapAnalyzer()

    gap_result = analyzer.analyze(
        integrated_result
    )

    print(
        "\nJOB TITLE"
    )

    print(
        "-" * 70
    )

    print(
        gap_result["job_title"]
    )

    summary = gap_result[
        "summary"
    ]

    print(
        "\nGAP SUMMARY"
    )

    print(
        "-" * 70
    )

    print(
        f"Total gaps: "
        f"{summary['total_gaps']}"
    )

    print(
        f"High priority: "
        f"{summary['high_priority_gaps']}"
    )

    print(
        f"Medium priority: "
        f"{summary['medium_priority_gaps']}"
    )

    print(
        f"Low priority: "
        f"{summary['low_priority_gaps']}"
    )

    print(
        f"Evidence improvements: "
        f"{summary['evidence_improvements']}"
    )

    print(
        "\nIDENTIFIED GAPS"
    )

    print(
        "-" * 70
    )

    for gap in gap_result[
        "gaps"
    ]:

        print(
            f"\nRequirement: "
            f"{gap['requirement']}"
        )

        print(
            f"Category: "
            f"{gap['category']}"
        )

        print(
            f"Priority: "
            f"{gap['priority']}"
        )

        print(
            f"Reason: "
            f"{gap['reason']}"
        )

        print(
            f"Suggested Action: "
            f"{gap['suggested_action']}"
        )

    print(
        "\nEVIDENCE IMPROVEMENTS"
    )

    print(
        "-" * 70
    )

    for improvement in gap_result[
        "evidence_improvements"
    ]:

        print(
            f"\nRequirement: "
            f"{improvement['requirement']}"
        )

        print(
            f"Category: "
            f"{improvement['category']}"
        )

        print(
            f"Type: "
            f"{improvement['type']}"
        )

        print(
            f"Priority: "
            f"{improvement['priority']}"
        )

        print(
            f"Reason: "
            f"{improvement['reason']}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "GAP ANALYSIS TEST: COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()