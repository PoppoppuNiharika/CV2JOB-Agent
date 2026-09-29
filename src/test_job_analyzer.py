from __future__ import annotations

import sys
from pathlib import Path

from job_analyzer import JobAnalyzer


BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

JD_PATH = (
    BASE_DIR
    / "test_job_description.txt"
)


def test_existing_job_description() -> None:

    analyzer = JobAnalyzer()

    if not JD_PATH.exists():

        raise FileNotFoundError(
            f"Test JD not found: {JD_PATH}"
        )

    text = JD_PATH.read_text(
        encoding="utf-8"
    )

    profile = analyzer.analyze(
        text
    )

    # ---------------------------------------------------------
    # Job title
    # ---------------------------------------------------------

    assert profile["job_title"], (
        "Job title was not extracted."
    )

    # ---------------------------------------------------------
    # Required skills
    # ---------------------------------------------------------

    expected_required = {
        "Python",
        "SQL",
        "Pandas",
        "NumPy",
        "Data Analysis",
        "Data Visualization",
        "Microsoft Excel",
        "Power BI",
    }

    actual_required = set(
        profile["required_skills"]
    )

    missing_required = (
        expected_required
        - actual_required
    )

    assert not missing_required, (
        "Missing required skills: "
        f"{sorted(missing_required)}"
    )

    # ---------------------------------------------------------
    # Preferred skills
    # ---------------------------------------------------------

    expected_preferred = {
        "Streamlit",
        "Scikit-learn",
        "Machine Learning",
        "Git",
        "GitHub",
    }

    actual_preferred = set(
        profile["preferred_skills"]
    )

    missing_preferred = (
        expected_preferred
        - actual_preferred
    )

    assert not missing_preferred, (
        "Missing preferred skills: "
        f"{sorted(missing_preferred)}"
    )

    # ---------------------------------------------------------
    # Soft skills
    # ---------------------------------------------------------

    assert (
        "Analytical Thinking"
        in profile["soft_skills"]
    )

    assert (
        "Problem Solving"
        in profile["soft_skills"]
    )

    # ---------------------------------------------------------
    # Responsibilities
    # ---------------------------------------------------------

    assert profile[
        "responsibilities"
    ], (
        "Responsibilities were not extracted."
    )

    # ---------------------------------------------------------
    # Education
    # ---------------------------------------------------------

    assert profile[
        "education_requirements"
    ], (
        "Education requirements were not extracted."
    )

    # ---------------------------------------------------------
    # Experience
    # ---------------------------------------------------------

    assert profile[
        "experience_requirements"
    ], (
        "Experience requirements were not extracted."
    )

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    assert (
        profile["location"]
    ), (
        "Location was not extracted."
    )


def test_unusual_headings() -> None:

    analyzer = JobAnalyzer()

    jd = """
    DATA SCIENCE INTERN

    Role Overview

    We are looking for a student to join our analyticsteam.

    Core Requirements

    - Python
    - SQL
    - Pandas
    - NumPy

    Nice-to-Have

    - Power BI
    - Streamlit

    What You'll Do

    - Analyze datasets.
    - Build dashboards.
    - Communicate findings with the team.

    Academic Qualifications

    - Currently pursuing a Bachelor's degree in Computer Science.

    Relevant Experience

    - Previous data analysis internship is preferred.

    Job Location

    Hyderabad, India
    """

    profile = analyzer.analyze(
        jd
    )

    assert (
        profile["job_title"]
        == "DATA SCIENCE INTERN"
    )

    assert "Python" in (
        profile["required_skills"]
    )

    assert "SQL" in (
        profile["required_skills"]
    )

    assert "Pandas" in (
        profile["required_skills"]
    )

    assert "NumPy" in (
        profile["required_skills"]
    )

    assert "Power BI" in (
        profile["preferred_skills"]
    )

    assert "Streamlit" in (
        profile["preferred_skills"]
    )

    assert profile[
        "responsibilities"
    ]

    assert profile[
        "education_requirements"
    ]

    assert profile[
        "experience_requirements"
    ]

    assert (
        "Hyderabad"
        in profile["location"]
    )


def test_no_explicit_requirement_headings() -> None:

    analyzer = JobAnalyzer()

    jd = """
    PYTHON DATA ANALYST INTERN

    We are looking for a student with strong Python,
    SQL and Pandas knowledge.

    The candidate must have experience with NumPy,
    data analysis and data visualization.

    Experience with Power BI is preferred.
    Streamlit is a nice to have.

    You will analyze large datasets, build dashboards,
    communicate insights and collaborate with the team.

    A Bachelor's degree in Computer Science or Data Science
    is required.

    Previous internship experience is preferred.

    Hyderabad, India
    """

    profile = analyzer.analyze(
        jd
    )

    required = set(
        profile["required_skills"]
    )

    assert "Python" in required

    assert "SQL" in required

    assert "Pandas" in required

    assert "NumPy" in required

    assert "Data Analysis" in required

    assert "Data Visualization" in required

    preferred = set(
        profile["preferred_skills"]
    )

    assert "Power BI" in preferred

    assert "Streamlit" in preferred

    assert profile[
        "responsibilities"
    ]

    assert profile[
        "education_requirements"
    ]

    assert profile[
        "experience_requirements"
    ]


def test_soft_skills_in_responsibilities() -> None:

    analyzer = JobAnalyzer()

    jd = """
    DATA ANALYST

    Responsibilities

    - Collaborate with cross-functional teams.
    - Communicate analytical findings clearly.
    - Apply critical thinking to business problems.
    - Demonstrate strong time management.
    - Work collaboratively with team members.

    Requirements

    - Python
    - SQL
    """

    profile = analyzer.analyze(
        jd
    )

    soft_skills = set(
        profile["soft_skills"]
    )

    assert (
        "Collaboration"
        in soft_skills
    )

    assert (
        "Communication"
        in soft_skills
    )

    assert (
        "Critical Thinking"
        in soft_skills
    )

    assert (
        "Time Management"
        in soft_skills
    )

    assert "Python" in (
        profile["required_skills"]
    )

    assert "SQL" in (
        profile["required_skills"]
    )


def test_skill_normalization() -> None:

    analyzer = JobAnalyzer()

    jd = """
    DATA ANALYST

    Required Skills

    - python
    - sql
    - numpy
    - excel
    - power bi

    Preferred Skills

    - scikit-learn
    """

    profile = analyzer.analyze(
        jd
    )

    required = profile[
        "required_skills"
    ]

    assert "Python" in required

    assert "SQL" in required

    assert "NumPy" in required

    assert (
        "Microsoft Excel"
        in required
    )

    assert "Power BI" in required

    assert (
        "Scikit-learn"
        in profile["preferred_skills"]
    )


def test_empty_job_description() -> None:

    analyzer = JobAnalyzer()

    try:

        analyzer.analyze("")

    except ValueError:

        return

    raise AssertionError(
        "Empty JD was not rejected."
    )


def main() -> None:

    analyzer = JobAnalyzer()

    print("=" * 70)
    print("JOB ANALYZER TEST")
    print("=" * 70)

    try:

        test_existing_job_description()

        print(
            "Existing JD test: PASS"
        )

        test_unusual_headings()

        print(
            "Unusual heading test: PASS"
        )

        test_no_explicit_requirement_headings()

        print(
            "No-heading JD test: PASS"
        )

        test_soft_skills_in_responsibilities()

        print(
            "Soft-skill responsibility test: PASS"
        )

        test_skill_normalization()

        print(
            "Skill normalization test: PASS"
        )

        test_empty_job_description()

        print(
            "Empty JD test: PASS"
        )

        print()
        print("=" * 70)
        print("JOB ANALYZER TEST: SUCCESS")
        print("=" * 70)

    except Exception as error:

        print()
        print("=" * 70)
        print("JOB ANALYZER TEST: FAILED")
        print("=" * 70)

        print(
            f"{type(error).__name__}: {error}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()