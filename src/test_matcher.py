from __future__ import annotations

from pathlib import Path

import pytest

from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from matcher import CVJobMatcher
from parser import CVParser


BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CV_PATH = (
    BASE_DIR / "test_cv.pdf"
)

JOB_PATH = (
    BASE_DIR / "test_job_description.txt"
)


# ==============================================================
# FIXTURES
# ==============================================================

@pytest.fixture
def analyzer() -> CVJobMatcher:
    return CVJobMatcher()


@pytest.fixture
def real_profiles() -> tuple[dict, dict]:
    """
    Build real CV and JD profiles using the actual parser and
    analyzers used by the project.
    """

    if not CV_PATH.exists():
        raise FileNotFoundError(
            f"Test CV not found: {CV_PATH}"
        )

    if not JOB_PATH.exists():
        raise FileNotFoundError(
            f"Test JD not found: {JOB_PATH}"
        )

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    cv_profile = CVAnalyzer().analyze(
        cv_text
    )

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    job_profile = JobAnalyzer().analyze(
        job_text
    )

    return (
        cv_profile,
        job_profile,
    )


# ==============================================================
# REAL CV/JD MATCHING
# ==============================================================

def test_real_cv_job_matching(
    analyzer: CVJobMatcher,
    real_profiles: tuple[dict, dict],
) -> None:

    cv_profile, job_profile = (
        real_profiles
    )

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    assert isinstance(
        result,
        dict,
    )

    assert (
        result["job_title"]
        == job_profile["job_title"]
    )

    assert isinstance(
        result["overall_match_percentage"],
        float,
    )

    assert (
        0.0
        <= result["overall_match_percentage"]
        <= 100.0
    )

    for category in (
        "required_skills",
        "preferred_skills",
        "soft_skills",
    ):

        group = result[category]

        assert isinstance(
            group,
            dict,
        )

        assert isinstance(
            group["matched"],
            list,
        )

        assert isinstance(
            group["missing"],
            list,
        )

        assert (
            group["total_required"]
            == (
                len(group["matched"])
                + len(group["missing"])
            )
        )

        assert (
            0.0
            <= group["match_percentage"]
            <= 100.0
        )


# ==============================================================
# REQUIRED SKILL MATCHING
# ==============================================================

def test_required_skill_matching(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "programming": [
                "Python",
                "SQL",
            ],
            "data_analysis": [
                "Pandas",
                "NumPy",
            ],
            "other": [],
        }
    }

    job_profile = {
        "job_title": "Test Role",
        "required_skills": [
            "Python",
            "SQL",
            "Pandas",
            "Power BI",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    required = result[
        "required_skills"
    ]

    assert set(
        required["matched"]
    ) == {
        "Python",
        "SQL",
        "Pandas",
    }

    assert (
        required["missing"]
        == ["Power BI"]
    )

    assert (
        required["match_percentage"]
        == 75.0
    )


# ==============================================================
# PREFERRED SKILL MATCHING
# ==============================================================

def test_preferred_skill_matching(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "programming": [
                "Python",
            ],
            "developer_tools": [
                "Git",
                "GitHub",
            ],
            "other": [],
        }
    }

    job_profile = {
        "job_title": "Test Role",
        "required_skills": [
            "Python",
        ],
        "preferred_skills": [
            "Git",
            "GitHub",
            "Docker",
        ],
        "soft_skills": [],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    preferred = result[
        "preferred_skills"
    ]

    assert set(
        preferred["matched"]
    ) == {
        "Git",
        "GitHub",
    }

    assert (
        preferred["missing"]
        == ["Docker"]
    )

    assert (
        preferred["match_percentage"]
        == round(
            2 / 3 * 100,
            2,
        )
    )


# ==============================================================
# SKILL NORMALIZATION
# ==============================================================

def test_skill_normalization(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "programming": [
                "python",
                "SQL",
            ],
            "data_analysis": [
                "Numpy",
            ],
            "other": [
                "Excel",
            ],
        }
    }

    job_profile = {
        "job_title": "Test Role",
        "required_skills": [
            "Python",
            "sql",
            "NumPy",
            "Microsoft Excel",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    required = result[
        "required_skills"
    ]

    assert set(
        required["matched"]
    ) == {
        "Python",
        "sql",
        "NumPy",
        "Microsoft Excel",
    }

    assert (
        required["missing"]
        == []
    )

    assert (
        required["match_percentage"]
        == 100.0
    )


# ==============================================================
# SOFT SKILL MATCHING
# ==============================================================

def test_soft_skill_matching(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "other": [
                "Analytical Thinking",
                "Problem Solving",
            ]
        },
        "raw_text": (
            "Strong analytical skills. "
            "Good communication and "
            "collaboration."
        ),
    }

    job_profile = {
        "job_title": "Test Role",
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [
            "Analytical Thinking",
            "Problem Solving",
            "Communication",
            "Collaboration",
        ],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    soft = result[
        "soft_skills"
    ]

    assert set(
        soft["matched"]
    ) == {
        "Analytical Thinking",
        "Problem Solving",
        "Communication",
        "Collaboration",
    }

    assert (
        soft["missing"]
        == []
    )

    assert (
        soft["match_percentage"]
        == 100.0
    )


# ==============================================================
# EMPTY REQUIREMENT GROUPS
# ==============================================================

def test_empty_requirement_groups(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "programming": [
                "Python",
            ]
        }
    }

    job_profile = {
        "job_title": "Python Role",
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    assert (
        result["overall_match_percentage"]
        == 0.0
    )

    assert (
        result["required_skills"][
            "match_percentage"
        ]
        == 0.0
    )


# ==============================================================
# DUPLICATE SKILLS
# ==============================================================

def test_duplicate_skills_are_removed(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "programming": [
                "Python",
                "python",
                "PYTHON",
            ]
        }
    }

    job_profile = {
        "job_title": "Test Role",
        "required_skills": [
            "Python",
            "python",
            "PYTHON",
        ],
        "preferred_skills": [],
        "soft_skills": [],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    required = result[
        "required_skills"
    ]

    assert (
        len(required["matched"])
        == 1
    )

    assert (
        required["matched"][0]
        == "Python"
    )

    assert (
        required["total_required"]
        == 1
    )

    assert (
        required["match_percentage"]
        == 100.0
    )


# ==============================================================
# INVALID INPUTS
# ==============================================================

def test_empty_cv_rejected(
    analyzer: CVJobMatcher,
) -> None:

    with pytest.raises(
        ValueError,
        match="CV profile is empty",
    ):
        analyzer.match(
            {},
            {
                "required_skills": [],
            },
        )


def test_empty_job_rejected(
    analyzer: CVJobMatcher,
) -> None:

    with pytest.raises(
        ValueError,
        match="Job profile is empty",
    ):
        analyzer.match(
            {
                "skills": {},
            },
            {},
        )


def test_non_dictionary_cv_rejected(
    analyzer: CVJobMatcher,
) -> None:

    with pytest.raises(
        TypeError,
        match="CV profile must be a dictionary",
    ):
        analyzer.match(
            [],
            {
                "required_skills": [],
            },
        )


# ==============================================================
# OVERALL SCORE
# ==============================================================

def test_overall_score_is_bounded(
    analyzer: CVJobMatcher,
) -> None:

    cv_profile = {
        "skills": {
            "programming": [
                "Python",
            ],
            "other": [
                "Problem Solving",
            ],
        }
    }

    job_profile = {
        "job_title": "Test Role",
        "required_skills": [
            "Python",
        ],
        "preferred_skills": [
            "Docker",
        ],
        "soft_skills": [
            "Problem Solving",
        ],
    }

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    score = result[
        "overall_match_percentage"
    ]

    assert (
        0.0
        <= score
        <= 100.0
    )


# ==============================================================
# STANDALONE TEST RUNNER
# ==============================================================

def main() -> None:

    print("=" * 70)
    print("CV ↔ JOB MATCHING TEST")
    print("=" * 70)

    analyzer = CVJobMatcher()

    cv_profile, job_profile = (
        _build_real_profiles()
    )

    result = analyzer.match(
        cv_profile,
        job_profile,
    )

    print()
    print("JOB TITLE")
    print("-" * 70)
    print(
        result["job_title"]
    )

    print()
    print("REQUIRED SKILLS")
    print("-" * 70)

    required = result[
        "required_skills"
    ]

    print(
        f"Match Percentage: "
        f"{required['match_percentage']}%"
    )

    print(
        "Matched: "
        f"{required['matched']}"
    )

    print(
        "Missing: "
        f"{required['missing']}"
    )

    print()
    print("PREFERRED SKILLS")
    print("-" * 70)

    preferred = result[
        "preferred_skills"
    ]

    print(
        f"Match Percentage: "
        f"{preferred['match_percentage']}%"
    )

    print(
        "Matched: "
        f"{preferred['matched']}"
    )

    print(
        "Missing: "
        f"{preferred['missing']}"
    )

    print()
    print("SOFT SKILLS")
    print("-" * 70)

    soft = result[
        "soft_skills"
    ]

    print(
        f"Match Percentage: "
        f"{soft['match_percentage']}%"
    )

    print(
        "Matched: "
        f"{soft['matched']}"
    )

    print(
        "Missing: "
        f"{soft['missing']}"
    )

    print()
    print("OVERALL MATCH")
    print("-" * 70)

    print(
        f"{result['overall_match_percentage']}%"
    )

    print()
    print("=" * 70)
    print("MATCHER TEST: SUCCESS")
    print("=" * 70)


def _build_real_profiles() -> tuple[
    dict,
    dict,
]:

    if not CV_PATH.exists():
        raise FileNotFoundError(
            f"Test CV not found: {CV_PATH}"
        )

    if not JOB_PATH.exists():
        raise FileNotFoundError(
            f"Test JD not found: {JOB_PATH}"
        )

    parser = CVParser()

    cv_text = parser.parse(
        CV_PATH
    )

    cv_profile = CVAnalyzer().analyze(
        cv_text
    )

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    job_profile = JobAnalyzer().analyze(
        job_text
    )

    return (
        cv_profile,
        job_profile,
    )


if __name__ == "__main__":
    main()