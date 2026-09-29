from pathlib import Path

import pytest

from parser import CVParser
from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from evidence_mapper import EvidenceMapper


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CV_PATH = BASE_DIR / "test_cv.pdf"
JOB_PATH = BASE_DIR / "test_job_description.txt"


# =========================================================
# FIXTURES
# =========================================================

@pytest.fixture(scope="module")
def cv_profile():
    """
    Build the structured CV profile once for the test module.
    """

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
def job_profile():
    """
    Build the structured job profile once for the test module.
    """

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    analyzer = JobAnalyzer()

    return analyzer.analyze(
        job_text
    )


@pytest.fixture
def mapper():
    return EvidenceMapper()


@pytest.fixture
def result(
    mapper,
    cv_profile,
    job_profile,
):
    return mapper.map_evidence(
        cv_profile,
        job_profile,
    )


# =========================================================
# HELPERS
# =========================================================

def find_requirement(
    result,
    requirement,
):
    """
    Find one requirement result.
    """

    for item in result["requirements"]:

        if item["requirement"] == requirement:
            return item

    raise AssertionError(
        f"Requirement not found: {requirement}"
    )


# =========================================================
# BASIC STRUCTURE
# =========================================================

def test_result_structure(result):

    assert isinstance(
        result,
        dict,
    )

    assert "job_title" in result
    assert "requirements" in result
    assert "summary" in result

    assert isinstance(
        result["requirements"],
        list,
    )

    assert isinstance(
        result["summary"],
        dict,
    )


# =========================================================
# REQUIREMENT COUNT
# =========================================================

def test_requirement_count(result):

    summary = result["summary"]

    assert (
        summary["total_requirements"]
        == 17
    )

    assert (
        summary["evidence_found"]
        + summary["gaps"]
        == summary["total_requirements"]
    )


# =========================================================
# PYTHON
# =========================================================

def test_python_evidence(result):

    item = find_requirement(
        result,
        "Python",
    )

    assert item["status"] == (
        "Evidence Found"
    )

    assert any(
        evidence["source"]
        == "Technical Skills"
        for evidence in item["evidence"]
    )


# =========================================================
# DATA ANALYSIS
# =========================================================

def test_data_analysis_evidence(result):

    item = find_requirement(
        result,
        "Data Analysis",
    )

    assert item["status"] == (
        "Evidence Found"
    )

    assert len(
        item["evidence"]
    ) >= 1


# =========================================================
# DATA VISUALIZATION
# =========================================================

def test_data_visualization_evidence(result):

    item = find_requirement(
        result,
        "Data Visualization",
    )

    assert item["status"] == (
        "Evidence Found"
    )

    assert any(
        evidence["source"]
        == "Project"
        for evidence in item["evidence"]
    )


# =========================================================
# MACHINE LEARNING GAP
# =========================================================

def test_machine_learning_is_gap(result):

    item = find_requirement(
        result,
        "Machine Learning",
    )

    assert item["status"] == "Gap"

    assert item["evidence"] == []


# =========================================================
# SCIKIT-LEARN GAP
# =========================================================

def test_scikit_learn_is_gap(result):

    item = find_requirement(
        result,
        "Scikit-learn",
    )

    assert item["status"] == "Gap"

    assert item["evidence"] == []


# =========================================================
# COMMUNICATION GAP
# =========================================================

def test_communication_is_gap(result):

    item = find_requirement(
        result,
        "Communication",
    )

    assert item["status"] == "Gap"

    assert item["evidence"] == []


# =========================================================
# COLLABORATION GAP
# =========================================================

def test_collaboration_is_gap(result):

    item = find_requirement(
        result,
        "Collaboration",
    )

    assert item["status"] == "Gap"

    assert item["evidence"] == []


# =========================================================
# NO GIANT RAW CV SNIPPETS
# =========================================================

def test_raw_cv_evidence_is_limited(result):

    for item in result["requirements"]:

        for evidence in item["evidence"]:

            if evidence["source"] == "CV Text":

                assert len(
                    evidence["text"]
                ) <= 280


# =========================================================
# NO DUPLICATE EVIDENCE
# =========================================================

def test_no_duplicate_evidence(result):

    for item in result["requirements"]:

        evidence = item["evidence"]

        normalized = [
            (
                entry["source"],
                entry["text"].strip().lower(),
            )
            for entry in evidence
        ]

        assert len(
            normalized
        ) == len(
            set(normalized)
        )


# =========================================================
# POWER BI DUPLICATE CHECK
# =========================================================

def test_power_bi_evidence_not_duplicated(result):

    item = find_requirement(
        result,
        "Power BI",
    )

    evidence_texts = [
        evidence["text"].strip().lower()
        for evidence in item["evidence"]
    ]

    assert evidence_texts.count(
        "power bi"
    ) == 1


# =========================================================
# EMPTY INPUT VALIDATION
# =========================================================

def test_empty_cv_rejected(mapper, job_profile):

    with pytest.raises(
        ValueError
    ):

        mapper.map_evidence(
            {},
            job_profile,
        )


def test_empty_job_rejected(mapper, cv_profile):

    with pytest.raises(
        ValueError
    ):

        mapper.map_evidence(
            cv_profile,
            {},
        )


def test_non_dictionary_cv_rejected(
    mapper,
    job_profile,
):

    with pytest.raises(
        TypeError
    ):

        mapper.map_evidence(
            [],
            job_profile,
        )


def test_non_dictionary_job_rejected(
    mapper,
    cv_profile,
):

    with pytest.raises(
        TypeError
    ):

        mapper.map_evidence(
            cv_profile,
            [],
        )


# =========================================================
# STANDALONE RUNNER
# =========================================================

def main():

    print(
        "=" * 70
    )

    print(
        "EVIDENCE MAPPING TEST"
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

    mapper = EvidenceMapper()

    result = mapper.map_evidence(
        cv_profile,
        job_profile,
    )

    print(
        "\nJOB TITLE"
    )

    print(
        "-" * 70
    )

    print(
        result["job_title"]
    )

    summary = result[
        "summary"
    ]

    print(
        "\nSUMMARY"
    )

    print(
        "-" * 70
    )

    print(
        f"Total requirements: "
        f"{summary['total_requirements']}"
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
        "\nREQUIREMENT EVIDENCE"
    )

    print(
        "-" * 70
    )

    for item in result[
        "requirements"
    ]:

        print(
            f"\n{item['category']}: "
            f"{item['requirement']}"
        )

        print(
            f"Status: "
            f"{item['status']}"
        )

        if item["evidence"]:

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
                "  - Evidence: None found"
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "EVIDENCE MAPPING TEST: COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()