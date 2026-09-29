from pathlib import Path

import pytest

from parser import CVParser
from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from integrated_matcher import IntegratedMatcher


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CV_PATH = BASE_DIR / "test_cv.pdf"
JOB_PATH = BASE_DIR / "test_job_description.txt"


# =========================================================
# STUB SEMANTIC MATCHER
# =========================================================

class StubSemanticMatcher:
    """
    Deterministic semantic matcher used to test the
    IntegratedMatcher decision logic.

    The real SemanticMatcher has already been tested separately.
    Here we test how IntegratedMatcher combines its results.
    """

    def __init__(
        self,
        scores=None,
    ):
        self.scores = scores or {}

    def compare(
        self,
        requirements,
        evidence,
    ):
        results = []

        for requirement in requirements:

            score_data = self.scores.get(
                requirement,
                {},
            )

            score = float(
                score_data.get(
                    "score",
                    0.0,
                )
            )

            best_evidence = score_data.get(
                "evidence",
                "",
            )

            if score >= 0.70:
                level = "Strong Evidence"

            elif score >= 0.50:
                level = "Related Evidence"

            elif score >= 0.35:
                level = "Weak Evidence"

            else:
                level = "No Meaningful Evidence"

            results.append(
                {
                    "requirement": requirement,
                    "best_evidence": best_evidence,
                    "similarity_score": score,
                    "match_level": level,
                }
            )

        return results


# =========================================================
# TEST PROFILES
# =========================================================

def make_cv_profile():
    """
    Small synthetic CV profile for isolated integration tests.
    """

    return {
        "summary": (
            "Computer science student with data analysis "
            "experience."
        ),
        "skills": {
            "programming": [
                "Python",
            ],
            "other": [
                "Problem Solving",
            ],
        },
        "experience": [
            "Used Python to analyze datasets."
        ],
        "projects": [
            "Built a dashboard using Python."
        ],
        "certifications": [],
        "activities": [],
        "raw_text": "",
    }


def make_job_profile():
    """
    Small synthetic job profile for isolated integration tests.
    """

    return {
        "job_title": "TEST ANALYST",
        "required_skills": [
            "Python",
            "SQL",
            "Data Analysis",
        ],
        "preferred_skills": [
            "Machine Learning",
        ],
        "soft_skills": [
            "Problem Solving",
        ],
    }


# =========================================================
# EXACT MATCH
# =========================================================

def test_exact_match_becomes_confirmed_match():

    semantic = StubSemanticMatcher(
        {
            "Python": {
                "score": 0.40,
                "evidence": "Python programming",
            },
        }
    )

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = make_cv_profile()

    job = {
        "job_title": "TEST",
        "required_skills": [
            "Python",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    item = result["requirements"][0]

    assert (
        item["status"]
        == "Confirmed Match"
    )

    assert (
        item["confidence"]
        == "High"
    )

    assert (
        item["basic_match"]
        == "Exact Match"
    )


# =========================================================
# EVIDENCE MATCH
# =========================================================

def test_explicit_evidence_with_related_semantics():

    semantic = StubSemanticMatcher(
        {
            "Data Analysis": {
                "score": 0.65,
                "evidence": (
                    "Analyzed datasets using Python."
                ),
            },
        }
    )

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = make_cv_profile()

    job = {
        "job_title": "TEST",
        "required_skills": [
            "Data Analysis",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    item = result["requirements"][0]

    assert (
        item["status"]
        == "Evidence Match"
    )

    assert (
        item["confidence"]
        == "High"
    )

    assert item["evidence"]


# =========================================================
# EVIDENCE FOUND
# =========================================================

def test_explicit_evidence_with_weak_semantics():

    semantic = StubSemanticMatcher(
        {
            "Data Analysis": {
                "score": 0.20,
                "evidence": "Some data work",
            },
        }
    )

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = make_cv_profile()

    job = {
        "job_title": "TEST",
        "required_skills": [
            "Data Analysis",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    item = result["requirements"][0]

    assert (
        item["status"]
        == "Evidence Found"
    )

    assert (
        item["confidence"]
        == "Medium"
    )


# =========================================================
# POTENTIAL MATCH
# =========================================================

def test_strong_semantics_without_explicit_evidence():

    semantic = StubSemanticMatcher(
        {
            "SQL": {
                "score": 0.85,
                "evidence": (
                    "Database querying experience"
                ),
            },
        }
    )

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = {
        "summary": "Software student.",
        "skills": {
            "programming": [
                "Python",
            ],
            "other": [],
        },
        "experience": [],
        "projects": [],
        "certifications": [],
        "activities": [],
        "raw_text": "",
    }

    job = {
        "job_title": "TEST",
        "required_skills": [
            "SQL",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    item = result["requirements"][0]

    assert (
        item["status"]
        == "Potential Match"
    )

    assert (
        item["confidence"]
        == "Medium"
    )

    assert (
        item["basic_match"]
        == "Not Exact Match"
    )


# =========================================================
# GAP
# =========================================================

def test_low_semantics_without_evidence_becomes_gap():

    semantic = StubSemanticMatcher(
        {
            "Machine Learning": {
                "score": 0.20,
                "evidence": "Unrelated text",
            },
        }
    )

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = {
        "summary": "Software student.",
        "skills": {
            "programming": [
                "Python",
            ],
            "other": [],
        },
        "experience": [],
        "projects": [],
        "certifications": [],
        "activities": [],
        "raw_text": "",
    }

    job = {
        "job_title": "TEST",
        "required_skills": [],
        "preferred_skills": [
            "Machine Learning",
        ],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    item = result["requirements"][0]

    assert (
        item["status"]
        == "Gap"
    )

    assert (
        item["confidence"]
        == "Low"
    )


# =========================================================
# REQUIREMENT DEDUPLICATION
# =========================================================

def test_requirements_are_deduplicated():

    semantic = StubSemanticMatcher()

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = make_cv_profile()

    job = {
        "job_title": "TEST",
        "required_skills": [
            "Python",
            "python",
            " Python ",
        ],
        "preferred_skills": [
            "PYTHON",
        ],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    requirements = [
        item["requirement"]
        for item in result["requirements"]
    ]

    assert requirements == [
        "Python",
    ]


# =========================================================
# SUMMARY COUNTS
# =========================================================

def test_summary_counts_are_consistent():

    semantic = StubSemanticMatcher(
        {
            "Python": {
                "score": 0.40,
                "evidence": "Python",
            },

            "Data Analysis": {
                "score": 0.65,
                "evidence": (
                    "Analyzed datasets"
                ),
            },

            "SQL": {
                "score": 0.85,
                "evidence": (
                    "Database analysis"
                ),
            },

            "Machine Learning": {
                "score": 0.10,
                "evidence": "",
            },
        }
    )

    matcher = IntegratedMatcher(
        semantic_matcher=semantic
    )

    cv = make_cv_profile()

    job = {
        "job_title": "TEST",
        "required_skills": [
            "Python",
            "Data Analysis",
        ],
        "preferred_skills": [
            "SQL",
            "Machine Learning",
        ],
        "soft_skills": [],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    summary = result["summary"]

    assert (
        summary["total_requirements"]
        == 4
    )

    assert (
        summary["confirmed_matches"]
        == 1
    )

    assert (
        summary["evidence_matches"]
        == 1
    )

    assert (
        summary["potential_matches"]
        == 1
    )

    assert (
        summary["gaps"]
        == 1
    )

    assert (
        summary["resolved_matches"]
        == 2
    )

    assert (
        summary["coverage_percentage"]
        == 75.0
    )


# =========================================================
# INPUT VALIDATION
# =========================================================

def test_empty_cv_rejected():

    matcher = IntegratedMatcher(
        semantic_matcher=StubSemanticMatcher()
    )

    with pytest.raises(
        ValueError
    ):

        matcher.analyze(
            {},
            make_job_profile(),
        )


def test_empty_job_rejected():

    matcher = IntegratedMatcher(
        semantic_matcher=StubSemanticMatcher()
    )

    with pytest.raises(
        ValueError
    ):

        matcher.analyze(
            make_cv_profile(),
            {},
        )


def test_non_dictionary_cv_rejected():

    matcher = IntegratedMatcher(
        semantic_matcher=StubSemanticMatcher()
    )

    with pytest.raises(
        TypeError
    ):

        matcher.analyze(
            [],
            make_job_profile(),
        )


def test_non_dictionary_job_rejected():

    matcher = IntegratedMatcher(
        semantic_matcher=StubSemanticMatcher()
    )

    with pytest.raises(
        TypeError
    ):

        matcher.analyze(
            make_cv_profile(),
            [],
        )


# =========================================================
# REQUIREMENT CATEGORY
# =========================================================

def test_requirement_category_is_preserved():

    matcher = IntegratedMatcher(
        semantic_matcher=StubSemanticMatcher()
    )

    cv = make_cv_profile()

    job = {
        "job_title": "TEST",
        "required_skills": [
            "Python",
        ],
        "preferred_skills": [
            "Machine Learning",
        ],
        "soft_skills": [
            "Problem Solving",
        ],
    }

    result = matcher.analyze(
        cv,
        job,
    )

    categories = {
        item["requirement"]: item["category"]
        for item in result["requirements"]
    }

    assert (
        categories["Python"]
        == "Required Skill"
    )

    assert (
        categories["Machine Learning"]
        == "Preferred Skill"
    )

    assert (
        categories["Problem Solving"]
        == "Soft Skill"
    )


# =========================================================
# REAL CV/JD FIXTURE
# =========================================================

@pytest.fixture(scope="module")
def real_cv_profile():

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    links = parser.extract_links(
        CV_PATH
    )

    analyzer = CVAnalyzer()

    return analyzer.analyze(
        cv_text,
        links=links,
    )


@pytest.fixture(scope="module")
def real_job_profile():

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    analyzer = JobAnalyzer()

    return analyzer.analyze(
        job_text
    )


# =========================================================
# REAL INTEGRATION SMOKE TEST
# =========================================================

def test_real_cv_jd_integration(
    real_cv_profile,
    real_job_profile,
):

    print(
        "\nLoading real integrated matching engine..."
    )

    matcher = IntegratedMatcher()

    result = matcher.analyze(
        real_cv_profile,
        real_job_profile,
    )

    # -----------------------------------------------------
    # Top-level structure
    # -----------------------------------------------------

    assert isinstance(
        result,
        dict,
    )

    assert set(
        result.keys()
    ) == {
        "job_title",
        "requirements",
        "summary",
        "basic_match",
        "evidence_mapping",
    }

    # -----------------------------------------------------
    # Requirement structure
    # -----------------------------------------------------

    assert isinstance(
        result["requirements"],
        list,
    )

    assert len(
        result["requirements"]
    ) == 17

    allowed_statuses = {
        "Confirmed Match",
        "Evidence Match",
        "Evidence Found",
        "Potential Match",
        "Gap",
    }

    allowed_confidence = {
        "High",
        "Medium",
        "Low",
    }

    for item in result[
        "requirements"
    ]:

        assert set(
            item.keys()
        ) == {
            "requirement",
            "category",
            "status",
            "confidence",
            "basic_match",
            "semantic_score",
            "semantic_level",
            "evidence",
            "best_semantic_evidence",
        }

        assert (
            item["status"]
            in allowed_statuses
        )

        assert (
            item["confidence"]
            in allowed_confidence
        )

        assert (
            item["basic_match"]
            in {
                "Exact Match",
                "Not Exact Match",
            }
        )

        assert (
            0.0
            <= item["semantic_score"]
            <= 1.0
        )

        assert isinstance(
            item["evidence"],
            list,
        )

    # -----------------------------------------------------
    # Summary consistency
    # -----------------------------------------------------

    summary = result[
        "summary"
    ]

    status_counts = {
        status: 0
        for status in allowed_statuses
    }

    for item in result[
        "requirements"
    ]:

        status_counts[
            item["status"]
        ] += 1

    assert (
        summary["total_requirements"]
        == len(
            result["requirements"]
        )
    )

    assert (
        summary["confirmed_matches"]
        == status_counts[
            "Confirmed Match"
        ]
    )

    assert (
        summary["evidence_matches"]
        == status_counts[
            "Evidence Match"
        ]
    )

    assert (
        summary["potential_matches"]
        == status_counts[
            "Potential Match"
        ]
    )

    assert (
        summary["gaps"]
        == status_counts[
            "Gap"
        ]
    )

    assert (
        summary["confirmed_matches"]
        + summary["evidence_matches"]
        + summary["potential_matches"]
        + summary["gaps"]
        == summary["total_requirements"]
    )

    assert (
        0.0
        <= summary["coverage_percentage"]
        <= 100.0
    )


# =========================================================
# REAL REQUIREMENT BEHAVIOR
# =========================================================

def test_real_python_is_confirmed_match(
    real_cv_profile,
    real_job_profile,
):

    matcher = IntegratedMatcher()

    result = matcher.analyze(
        real_cv_profile,
        real_job_profile,
    )

    python_item = next(
        item
        for item in result["requirements"]
        if item["requirement"]
        == "Python"
    )

    assert (
        python_item["status"]
        == "Confirmed Match"
    )

    assert (
        python_item["confidence"]
        == "High"
    )


def test_real_machine_learning_remains_gap(
    real_cv_profile,
    real_job_profile,
):

    matcher = IntegratedMatcher()

    result = matcher.analyze(
        real_cv_profile,
        real_job_profile,
    )

    ml_item = next(
        item
        for item in result["requirements"]
        if item["requirement"]
        == "Machine Learning"
    )

    assert (
        ml_item["status"]
        == "Gap"
    )

    assert (
        ml_item["evidence"]
        == []
    )


# =========================================================
# STANDALONE DEMONSTRATION
# =========================================================

def main():

    print(
        "=" * 70
    )

    print(
        "INTEGRATED CV <-> JOB ANALYSIS TEST"
    )

    print(
        "=" * 70
    )

    # -----------------------------------------------------
    # Parse CV
    # -----------------------------------------------------

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    links = parser.extract_links(
        CV_PATH
    )

    # -----------------------------------------------------
    # Analyze CV
    # -----------------------------------------------------

    cv_analyzer = CVAnalyzer()

    cv_profile = cv_analyzer.analyze(
        cv_text,
        links=links,
    )

    # -----------------------------------------------------
    # Analyze JD
    # -----------------------------------------------------

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    job_analyzer = JobAnalyzer()

    job_profile = job_analyzer.analyze(
        job_text
    )

    # -----------------------------------------------------
    # Run integrated matcher
    # -----------------------------------------------------

    print(
        "\nLoading integrated matching engine..."
    )

    matcher = IntegratedMatcher()

    result = matcher.analyze(
        cv_profile,
        job_profile,
    )

    # -----------------------------------------------------
    # Job
    # -----------------------------------------------------

    print(
        "\nJOB TITLE"
    )

    print(
        "-" * 70
    )

    print(
        result["job_title"]
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    summary = result[
        "summary"
    ]

    print(
        "\nFINAL SUMMARY"
    )

    print(
        "-" * 70
    )

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
        f"Coverage: "
        f"{summary['coverage_percentage']}%"
    )

    # -----------------------------------------------------
    # Requirements
    # -----------------------------------------------------

    print(
        "\nREQUIREMENT ANALYSIS"
    )

    print(
        "-" * 70
    )

    for item in result[
        "requirements"
    ]:

        print(
            f"\nRequirement: "
            f"{item['requirement']}"
        )

        print(
            f"Category: "
            f"{item['category']}"
        )

        print(
            f"Status: "
            f"{item['status']}"
        )

        print(
            f"Confidence: "
            f"{item['confidence']}"
        )

        print(
            f"Basic Match: "
            f"{item['basic_match']}"
        )

        print(
            f"Semantic Score: "
            f"{item['semantic_score']}"
        )

        print(
            f"Semantic Level: "
            f"{item['semantic_level']}"
        )

        if item["evidence"]:

            print(
                "Explicit Evidence:"
            )

            for evidence in item[
                "evidence"
            ]:

                print(
                    f"  - "
                    f"[{evidence['source']}] "
                    f"{evidence['text']}"
                )

        else:

            print(
                "Explicit Evidence: None"
            )

        print(
            "Best Semantic Evidence: "
            f"{item['best_semantic_evidence']}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "INTEGRATED MATCHER TEST: COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()