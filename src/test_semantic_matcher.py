from pathlib import Path

import numpy as np
import pytest

from parser import CVParser
from cv_analyzer import CVAnalyzer
from job_analyzer import JobAnalyzer
from semantic_matcher import SemanticMatcher


# =========================================================
# FILE PATHS
# =========================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

CV_PATH = BASE_DIR / "test_cv.pdf"
JOB_PATH = BASE_DIR / "test_job_description.txt"


# =========================================================
# TEST EMBEDDING MODEL
# =========================================================

class FakeEmbeddingModel:
    """
    Small deterministic embedding model used for unit tests.

    It mimics the SentenceTransformer.encode() interface.

    This allows us to test the SemanticMatcher logic without
    downloading/loading an ML model for every unit test.
    """

    def encode(
        self,
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ):
        vectors = []

        for text in texts:

            normalized = text.lower()

            # ---------------------------------------------
            # Python
            # ---------------------------------------------

            if "python" in normalized:

                vector = [
                    1.0,
                    0.0,
                    0.0,
                ]

            # ---------------------------------------------
            # SQL
            # ---------------------------------------------

            elif "sql" in normalized:

                vector = [
                    0.0,
                    1.0,
                    0.0,
                ]

            # ---------------------------------------------
            # Visualization
            # ---------------------------------------------

            elif (
                "visualization" in normalized
                or "visualisations" in normalized
                or "visualization" in normalized
                or "charts" in normalized
            ):

                vector = [
                    0.0,
                    0.0,
                    1.0,
                ]

            # ---------------------------------------------
            # Generic/unrelated text
            # ---------------------------------------------

            else:

                vector = [
                    0.2,
                    0.2,
                    0.0,
                ]

            vectors.append(
                vector
            )

        result = np.array(
            vectors,
            dtype=float,
        )

        if normalize_embeddings:

            norms = np.linalg.norm(
                result,
                axis=1,
                keepdims=True,
            )

            result = result / np.maximum(
                norms,
                1e-12,
            )

        return result


# =========================================================
# FIXTURES
# =========================================================

@pytest.fixture
def fake_matcher():

    return SemanticMatcher(
        model=FakeEmbeddingModel()
    )


@pytest.fixture(scope="module")
def cv_profile():

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

    job_text = JOB_PATH.read_text(
        encoding="utf-8"
    )

    analyzer = JobAnalyzer()

    return analyzer.analyze(
        job_text
    )


# =========================================================
# HELPERS
# =========================================================

def build_cv_evidence(
    cv_profile: dict,
) -> list[str]:
    """
    Build semantic evidence from the structured CV profile.

    This mirrors the type of evidence that the production
    IntegratedMatcher sends to SemanticMatcher.
    """

    evidence = []

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    summary = cv_profile.get(
        "summary",
        "",
    )

    if isinstance(
        summary,
        str,
    ) and summary.strip():

        evidence.append(
            summary
        )

    # -----------------------------------------------------
    # Experience
    # -----------------------------------------------------

    _collect_structured_text(
        cv_profile.get(
            "experience",
            [],
        ),
        evidence,
    )

    # -----------------------------------------------------
    # Projects
    # -----------------------------------------------------

    _collect_structured_text(
        cv_profile.get(
            "projects",
            [],
        ),
        evidence,
    )

    # -----------------------------------------------------
    # Certifications
    # -----------------------------------------------------

    _collect_structured_text(
        cv_profile.get(
            "certifications",
            [],
        ),
        evidence,
    )

    # -----------------------------------------------------
    # Activities
    # -----------------------------------------------------

    _collect_structured_text(
        cv_profile.get(
            "activities",
            [],
        ),
        evidence,
    )

    # -----------------------------------------------------
    # Technical skills
    # -----------------------------------------------------

    skills = cv_profile.get(
        "skills",
        {},
    )

    if isinstance(
        skills,
        dict,
    ):

        for category, values in skills.items():

            if not isinstance(
                values,
                list,
            ):
                continue

            for value in values:

                if isinstance(
                    value,
                    str,
                ):

                    evidence.append(
                        f"{category}: {value}"
                    )

    return _clean_text_items(
        evidence
    )


def _collect_structured_text(
    items,
    evidence,
):
    """
    Extract strings from structured CV sections.
    """

    if not isinstance(
        items,
        list,
    ):
        return

    for item in items:

        if isinstance(
            item,
            str,
        ):

            evidence.append(
                item
            )

            continue

        if not isinstance(
            item,
            dict,
        ):
            continue

        for value in item.values():

            if isinstance(
                value,
                str,
            ):

                evidence.append(
                    value
                )

            elif isinstance(
                value,
                list,
            ):

                for nested in value:

                    if isinstance(
                        nested,
                        str,
                    ):

                        evidence.append(
                            nested
                        )


def _clean_text_items(
    items,
):
    """
    Normalize and deduplicate text items.
    """

    cleaned = []

    seen = set()

    for item in items:

        if not isinstance(
            item,
            str,
        ):
            continue

        normalized = " ".join(
            item.split()
        ).strip()

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            continue

        seen.add(
            key
        )

        cleaned.append(
            normalized
        )

    return cleaned


# =========================================================
# BASIC STRUCTURE TEST
# =========================================================

def test_empty_requirements_returns_empty(
    fake_matcher,
):

    result = fake_matcher.compare(
        [],
        [
            "Python programming",
        ],
    )

    assert result == []


# =========================================================
# NO EVIDENCE TEST
# =========================================================

def test_no_evidence_returns_no_evidence_results(
    fake_matcher,
):

    result = fake_matcher.compare(
        [
            "Python",
            "SQL",
        ],
        [],
    )

    assert len(result) == 2

    for item in result:

        assert item["best_evidence"] == ""

        assert (
            item["similarity_score"]
            == 0.0
        )

        assert (
            item["match_level"]
            == "No Evidence"
        )


# =========================================================
# EXACT SEMANTIC MATCH TEST
# =========================================================

def test_exact_semantic_match(
    fake_matcher,
):

    result = fake_matcher.compare(
        [
            "Python",
        ],
        [
            "Python programming",
            "SQL database querying",
        ],
    )

    assert len(result) == 1

    item = result[0]

    assert (
        item["requirement"]
        == "Python"
    )

    assert (
        item["best_evidence"]
        == "Python programming"
    )

    assert (
        item["similarity_score"]
        == 1.0
    )

    assert (
        item["match_level"]
        == "Strong Evidence"
    )


# =========================================================
# BEST EVIDENCE SELECTION TEST
# =========================================================

def test_best_evidence_is_selected(
    fake_matcher,
):

    result = fake_matcher.compare(
        [
            "Data Visualization",
        ],
        [
            "SQL database querying",
            "Created charts and data visualizations",
            "General college activity",
        ],
    )

    item = result[0]

    assert (
        item["best_evidence"]
        == "Created charts and data visualizations"
    )

    assert (
        item["similarity_score"]
        > 0.80
    )


# =========================================================
# DUPLICATE REQUIREMENT TEST
# =========================================================

def test_duplicate_requirements_are_removed(
    fake_matcher,
):

    result = fake_matcher.compare(
        [
            "Python",
            "Python",
            " python ",
            "SQL",
        ],
        [
            "Python programming",
            "SQL querying",
        ],
    )

    assert len(result) == 2

    requirements = [
        item["requirement"]
        for item in result
    ]

    assert requirements == [
        "Python",
        "SQL",
    ]


# =========================================================
# DUPLICATE EVIDENCE TEST
# =========================================================

def test_duplicate_evidence_is_removed(
    fake_matcher,
):

    result = fake_matcher.compare(
        [
            "Python",
        ],
        [
            "Python programming",
            "Python programming",
            " python programming ",
        ],
    )

    assert len(result) == 1

    assert (
        result[0]["best_evidence"]
        == "Python programming"
    )


# =========================================================
# SCORE CLASSIFICATION TESTS
# =========================================================

@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (
            0.90,
            "Strong Evidence",
        ),
        (
            0.70,
            "Strong Evidence",
        ),
        (
            0.60,
            "Related Evidence",
        ),
        (
            0.50,
            "Related Evidence",
        ),
        (
            0.40,
            "Weak Evidence",
        ),
        (
            0.35,
            "Weak Evidence",
        ),
        (
            0.20,
            "No Meaningful Evidence",
        ),
        (
            0.0,
            "No Meaningful Evidence",
        ),
    ],
)
def test_score_classification(
    score,
    expected,
):

    assert (
        SemanticMatcher._classify_score(
            score
        )
        == expected
    )


# =========================================================
# INVALID SCORE TESTS
# =========================================================

def test_invalid_score_classification():

    assert (
        SemanticMatcher._classify_score(
            float("nan")
        )
        == "No Meaningful Evidence"
    )

    assert (
        SemanticMatcher._classify_score(
            float("inf")
        )
        == "No Meaningful Evidence"
    )


# =========================================================
# INPUT VALIDATION TESTS
# =========================================================

def test_invalid_requirements_type(
    fake_matcher,
):

    with pytest.raises(
        TypeError
    ):

        fake_matcher.compare(
            "Python",
            [
                "Python programming",
            ],
        )


def test_invalid_evidence_type(
    fake_matcher,
):

    with pytest.raises(
        TypeError
    ):

        fake_matcher.compare(
            [
                "Python",
            ],
            "Python programming",
        )


def test_invalid_requirement_item(
    fake_matcher,
):

    with pytest.raises(
        TypeError
    ):

        fake_matcher.compare(
            [
                "Python",
                123,
            ],
            [
                "Python programming",
            ],
        )


def test_invalid_evidence_item(
    fake_matcher,
):

    with pytest.raises(
        TypeError
    ):

        fake_matcher.compare(
            [
                "Python",
            ],
            [
                "Python programming",
                None,
            ],
        )


# =========================================================
# MODEL NAME VALIDATION
# =========================================================

def test_empty_model_name_rejected():

    with pytest.raises(
        ValueError
    ):

        SemanticMatcher(
            model_name="",
            model=FakeEmbeddingModel(),
        )


# =========================================================
# REAL CV EVIDENCE BUILD TEST
# =========================================================

def test_real_cv_evidence_is_built(
    cv_profile,
):

    evidence = build_cv_evidence(
        cv_profile
    )

    assert isinstance(
        evidence,
        list,
    )

    assert len(
        evidence
    ) > 0

    combined = " ".join(
        evidence
    ).lower()

    assert "python" in combined
    assert "streamlit" in combined


# =========================================================
# REAL JOB REQUIREMENTS TEST
# =========================================================

def test_real_job_requirements_exist(
    job_profile,
):

    requirements = []

    for category in (
        "required_skills",
        "preferred_skills",
        "soft_skills",
    ):

        requirements.extend(
            job_profile.get(
                category,
                [],
            )
        )

    assert len(
        requirements
    ) > 0

    assert "Python" in requirements
    assert "SQL" in requirements


# =========================================================
# REAL MODEL SMOKE TEST
# =========================================================

def test_real_model_smoke_test(
    cv_profile,
    job_profile,
):

    evidence = build_cv_evidence(
        cv_profile
    )

    requirements = [
        "Python",
        "Data Visualization",
        "Machine Learning",
    ]

    matcher = SemanticMatcher()

    results = matcher.compare(
        requirements,
        evidence,
    )

    assert len(results) == 3

    for result in results:

        assert isinstance(
            result,
            dict,
        )

        assert set(
            result.keys()
        ) == {
            "requirement",
            "best_evidence",
            "similarity_score",
            "match_level",
        }

        assert isinstance(
            result["requirement"],
            str,
        )

        assert isinstance(
            result["best_evidence"],
            str,
        )

        assert isinstance(
            result["similarity_score"],
            float,
        )

        assert -1.0 <= (
            result["similarity_score"]
        ) <= 1.0

        assert result[
            "match_level"
        ] in {
            "No Evidence",
            "Strong Evidence",
            "Related Evidence",
            "Weak Evidence",
            "No Meaningful Evidence",
        }


# =========================================================
# REAL MODEL RELEVANCE TEST
# =========================================================

def test_real_model_finds_visualization_evidence(
    cv_profile,
):

    evidence = build_cv_evidence(
        cv_profile
    )

    matcher = SemanticMatcher()

    results = matcher.compare(
        [
            "Data Visualization",
        ],
        evidence,
    )

    assert len(results) == 1

    result = results[0]

    assert (
        result["best_evidence"]
        != ""
    )

    # The best evidence should contain meaningful
    # visualization-related wording from the CV.
    evidence_text = (
        result["best_evidence"]
        .lower()
    )

    assert any(
        phrase in evidence_text
        for phrase in (
            "visualization",
            "visualizations",
            "matplotlib",
            "seaborn",
            "dashboard",
        )
    )


# =========================================================
# STANDALONE DEMONSTRATION
# =========================================================

def main():

    print(
        "=" * 70
    )

    print(
        "SEMANTIC MATCHING TEST"
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
    # Build evidence
    # -----------------------------------------------------

    cv_evidence = build_cv_evidence(
        cv_profile
    )

    # -----------------------------------------------------
    # Load model
    # -----------------------------------------------------

    print(
        "\nLoading semantic model..."
    )

    print(
        "Model: all-MiniLM-L6-v2"
    )

    matcher = SemanticMatcher()

    # -----------------------------------------------------
    # Requirements
    # -----------------------------------------------------

    requirements = []

    for category in (
        "required_skills",
        "preferred_skills",
        "soft_skills",
    ):

        requirements.extend(
            job_profile.get(
                category,
                [],
            )
        )

    # -----------------------------------------------------
    # Compare
    # -----------------------------------------------------

    results = matcher.compare(
        requirements,
        cv_evidence,
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print(
        "\nJOB TITLE"
    )

    print(
        "-" * 70
    )

    print(
        job_profile.get(
            "job_title",
            "",
        )
    )

    print(
        "\nCV EVIDENCE ITEMS"
    )

    print(
        "-" * 70
    )

    print(
        f"Total evidence items: "
        f"{len(cv_evidence)}"
    )

    print(
        "\nSEMANTIC RESULTS"
    )

    print(
        "-" * 70
    )

    for result in results:

        print(
            f"\nRequirement: "
            f"{result['requirement']}"
        )

        print(
            f"Similarity: "
            f"{result['similarity_score']}"
        )

        print(
            f"Level: "
            f"{result['match_level']}"
        )

        print(
            f"Best Evidence: "
            f"{result['best_evidence']}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "SEMANTIC MATCHING TEST: COMPLETE"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()