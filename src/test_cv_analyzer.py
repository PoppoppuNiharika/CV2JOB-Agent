from __future__ import annotations

import sys
from pathlib import Path

from cv_analyzer import CVAnalyzer
from parser import CVParser


BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CV_PATH = (
    BASE_DIR / "test_cv.pdf"
)


def test_real_cv() -> None:

    if not CV_PATH.exists():

        raise FileNotFoundError(
            f"Test CV not found: {CV_PATH}"
        )

    parser = CVParser()
    analyzer = CVAnalyzer()

    text, links = (
        parser.parse_with_links(
            CV_PATH
        )
    )

    profile = analyzer.analyze(
        text,
        links=links,
    )

    # ---------------------------------------------------------
    # Basic profile validation
    # ---------------------------------------------------------

    assert profile["raw_text"], (
        "raw_text should not be empty."
    )

    assert profile["name"], (
        "Name extraction failed."
    )

    assert profile["contact"]["email"], (
        "Email extraction failed."
    )

    assert profile["contact"]["phone"], (
        "Phone extraction failed."
    )

    # ---------------------------------------------------------
    # Skills
    # ---------------------------------------------------------

    all_skills = []

    for skills in profile[
        "skills"
    ].values():

        all_skills.extend(
            skills
        )

    expected_skills = {
        "Python",
        "SQL",
        "Pandas",
        "NumPy",
        "Matplotlib",
        "Seaborn",
        "Power BI",
        "Microsoft Excel",
        "Streamlit",
        "Git",
        "GitHub",
    }

    missing_skills = (
        expected_skills
        - set(all_skills)
    )

    assert not missing_skills, (
        "Expected skills were not detected: "
        f"{sorted(missing_skills)}"
    )

    # ---------------------------------------------------------
    # Education
    # ---------------------------------------------------------

    assert profile["education"], (
        "Education section was not extracted."
    )

    # ---------------------------------------------------------
    # Experience
    # ---------------------------------------------------------

    assert profile["experience"], (
        "Experience section was not extracted."
    )

    # ---------------------------------------------------------
    # Projects
    # ---------------------------------------------------------

    assert profile["projects"], (
        "Projects were not extracted."
    )

    # ---------------------------------------------------------
    # Certifications
    # ---------------------------------------------------------

    assert profile["certifications"], (
        "Certifications were not extracted."
    )

    # ---------------------------------------------------------
    # Activities
    # ---------------------------------------------------------

    assert profile["activities"], (
        "Activities were not extracted."
    )

    # ---------------------------------------------------------
    # Languages
    # ---------------------------------------------------------

    assert profile["languages"], (
        "Languages were not extracted."
    )

    return


def test_heading_variations() -> None:

    analyzer = CVAnalyzer()

    sample_cv = """
    JANE DOE

    jane@example.com
    +1 555 123 4567

    1. Professional Summary
    Data science student interested in analytics.

    2. Education
    B.Tech Computer Science

    3. Skills & Technologies
    Python
    SQL
    Pandas

    4. Work Experience
    Data Analyst Intern
    Analyzed datasets.

    5. Selected Projects
    Sales Dashboard
    Built an interactive dashboard.

    6. Certifications
    Python Certificate

    7. Extracurricular Activities
    Member of Coding Club

    8. Languages
    English
    Telugu
    """

    profile = analyzer.analyze(
        sample_cv
    )

    assert (
        profile["name"]
        == "JANE DOE"
    )

    assert (
        profile["contact"]["email"]
        == "jane@example.com"
    )

    assert profile["contact"]["phone"], (
        "Phone number was not detected."
    )

    assert profile["summary"]

    assert profile["education"]

    assert (
        "Python"
        in profile["skills"]["programming"]
    )

    assert (
        "SQL"
        in profile["skills"]["programming"]
    )

    assert profile["experience"]

    assert profile["projects"]

    assert profile["certifications"]

    assert profile["activities"]

    assert profile["languages"]


def test_combined_sections() -> None:

    analyzer = CVAnalyzer()

    sample_cv = """
    ALEX SMITH

    Experience & Selected Projects

    Data Analyst Intern
    Worked with structured datasets.

    Project: Customer Churn Dashboard
    Built a dashboard using Python and Power BI.

    Certifications & Activities

    Google Data Analytics Certificate

    Member of Data Science Club
    """

    profile = analyzer.analyze(
        sample_cv
    )

    assert profile["experience"], (
        "Experience from combined section "
        "was not extracted."
    )

    assert profile["projects"], (
        "Project from combined section "
        "was not extracted."
    )

    assert profile["certifications"], (
        "Certification from combined section "
        "was not extracted."
    )

    assert profile["activities"], (
        "Activity from combined section "
        "was not extracted."
    )


def main() -> None:

    print("=" * 70)
    print("CV ANALYZER TEST")
    print("=" * 70)

    try:

        test_real_cv()

        print(
            "Real CV analysis: PASS"
        )

        test_heading_variations()

        print(
            "Heading variation test: PASS"
        )

        test_combined_sections()

        print(
            "Combined section test: PASS"
        )

        print()
        print("=" * 70)
        print("CV ANALYZER TEST: SUCCESS")
        print("=" * 70)

    except Exception as error:

        print()
        print("=" * 70)
        print("CV ANALYZER TEST: FAILED")
        print("=" * 70)

        print(
            f"{type(error).__name__}: {error}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()