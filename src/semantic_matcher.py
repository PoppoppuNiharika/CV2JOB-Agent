from typing import Any
import math


from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticMatcher:
    """
    Compare job requirements with CV evidence using
    sentence embeddings and cosine similarity.

    This layer adds semantic understanding to the
    deterministic matching system.

    Important:
    Semantic similarity indicates textual/contextual
    relatedness. It does not independently prove that
    a candidate possesses a skill.

    The output interface is intentionally kept compatible
    with IntegratedMatcher.
    """

    # =========================================================
    # SEMANTIC THRESHOLDS
    # =========================================================

    STRONG_THRESHOLD = 0.70
    RELATED_THRESHOLD = 0.50
    WEAK_THRESHOLD = 0.35

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        model: Any | None = None,
    ):
        """
        Initialize the semantic matcher.

        Args:
            model_name:
                Hugging Face sentence-transformer model name.

            model:
                Optional preloaded/test model.

                When supplied, the matcher uses it directly.
                This is useful for deterministic unit testing
                and avoids loading the real embedding model
                during isolated tests.
        """

        if not isinstance(
            model_name,
            str,
        ) or not model_name.strip():

            raise ValueError(
                "model_name must be a non-empty string."
            )

        self.model_name = model_name.strip()

        # -----------------------------------------------------
        # Dependency injection
        # -----------------------------------------------------

        if model is not None:

            self.model = model

        else:

            try:

                self.model = SentenceTransformer(
                    self.model_name
                )

            except Exception as error:

                raise RuntimeError(
                    "Unable to load the semantic embedding "
                    f"model '{self.model_name}'. "
                    "Check the model name, installed "
                    "dependencies, network access, or "
                    "local Hugging Face model cache."
                ) from error

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def compare(
        self,
        requirements: list[str],
        evidence: list[str],
    ) -> list[dict[str, Any]]:
        """
        Compare every job requirement against CV evidence.

        Args:
            requirements:
                List of job requirements.

            evidence:
                List of CV evidence statements.

        Returns:
            One result dictionary per unique non-empty
            requirement.

        Output format:

            {
                "requirement": str,
                "best_evidence": str,
                "similarity_score": float,
                "match_level": str,
            }

        Semantic similarity alone should not be interpreted
        as proof of a skill. IntegratedMatcher applies the
        deterministic/evidence layers alongside this result.
        """

        cleaned_requirements = self._clean_items(
            requirements
        )

        cleaned_evidence = self._clean_items(
            evidence
        )

        # -----------------------------------------------------
        # No requirements
        # -----------------------------------------------------

        if not cleaned_requirements:

            return []

        # -----------------------------------------------------
        # No evidence
        # -----------------------------------------------------

        if not cleaned_evidence:

            return [
                {
                    "requirement": requirement,
                    "best_evidence": "",
                    "similarity_score": 0.0,
                    "match_level": "No Evidence",
                }
                for requirement in cleaned_requirements
            ]

        # -----------------------------------------------------
        # Create embeddings
        # -----------------------------------------------------

        try:

            requirement_embeddings = self.model.encode(
                cleaned_requirements,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            evidence_embeddings = self.model.encode(
                cleaned_evidence,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

        except Exception as error:

            raise RuntimeError(
                "Semantic embedding generation failed."
            ) from error

        # -----------------------------------------------------
        # Validate embeddings
        # -----------------------------------------------------

        self._validate_embeddings(
            requirement_embeddings,
            "requirement",
        )

        self._validate_embeddings(
            evidence_embeddings,
            "evidence",
        )

        # -----------------------------------------------------
        # Calculate cosine similarities
        # -----------------------------------------------------

        try:

            similarity_matrix = cosine_similarity(
                requirement_embeddings,
                evidence_embeddings,
            )

        except Exception as error:

            raise RuntimeError(
                "Cosine similarity calculation failed."
            ) from error

        # -----------------------------------------------------
        # Build result for each requirement
        # -----------------------------------------------------

        results = []

        for index, requirement in enumerate(
            cleaned_requirements
        ):

            similarities = similarity_matrix[
                index
            ]

            best_index = int(
                similarities.argmax()
            )

            best_score = float(
                similarities[best_index]
            )

            # Protect against unexpected numerical issues.
            if not math.isfinite(
                best_score
            ):

                best_score = 0.0

            # Cosine similarity can theoretically be in
            # [-1, 1]. Small floating-point overshoots are
            # safely bounded.
            best_score = max(
                -1.0,
                min(
                    1.0,
                    best_score,
                ),
            )

            best_evidence = cleaned_evidence[
                best_index
            ]

            results.append(
                {
                    "requirement": requirement,
                    "best_evidence": best_evidence,
                    "similarity_score": round(
                        best_score,
                        4,
                    ),
                    "match_level": self._classify_score(
                        best_score
                    ),
                }
            )

        return results

    # =========================================================
    # SCORE CLASSIFICATION
    # =========================================================

    @classmethod
    def _classify_score(
        cls,
        score: float,
    ) -> str:
        """
        Convert a cosine similarity score into an
        interpretable semantic level.

        Thresholds are intentionally kept in one place
        so downstream code has a stable interpretation.
        """

        if not isinstance(
            score,
            (int, float),
        ):

            return "No Meaningful Evidence"

        if not math.isfinite(
            float(score)
        ):

            return "No Meaningful Evidence"

        if score >= cls.STRONG_THRESHOLD:

            return "Strong Evidence"

        if score >= cls.RELATED_THRESHOLD:

            return "Related Evidence"

        if score >= cls.WEAK_THRESHOLD:

            return "Weak Evidence"

        return "No Meaningful Evidence"

    # =========================================================
    # INPUT CLEANING
    # =========================================================

    @staticmethod
    def _clean_items(
        items: Any,
    ) -> list[str]:
        """
        Clean, validate, and deduplicate string items.

        Original ordering is preserved.
        """

        if items is None:
            return []

        if not isinstance(
            items,
            (list, tuple),
        ):

            raise TypeError(
                "Semantic matcher inputs must be lists "
                "or tuples of strings."
            )

        cleaned = []

        seen = set()

        for item in items:

            if not isinstance(
                item,
                str,
            ):

                raise TypeError(
                    "Every semantic matcher item "
                    "must be a string."
                )

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
    # EMBEDDING VALIDATION
    # =========================================================

    @staticmethod
    def _validate_embeddings(
        embeddings: Any,
        label: str,
    ) -> None:
        """
        Validate the basic shape of generated embeddings.
        """

        shape = getattr(
            embeddings,
            "shape",
            None,
        )

        if shape is None:

            raise RuntimeError(
                f"The {label} embeddings do not expose "
                "a valid shape."
            )

        if len(shape) != 2:

            raise RuntimeError(
                f"The {label} embeddings must be a "
                "2-dimensional matrix."
            )

        if shape[0] == 0 or shape[1] == 0:

            raise RuntimeError(
                f"The {label} embeddings are empty."
            )

        # Check for NaN / infinity values when supported.
        try:

            import numpy as np

            if not np.isfinite(
                embeddings
            ).all():

                raise RuntimeError(
                    f"The {label} embeddings contain "
                    "NaN or infinite values."
                )

        except ImportError:
            # NumPy is already a dependency of the project,
            # but this guard keeps the method defensive.
            pass


if __name__ == "__main__":

    print(
        "SemanticMatcher is ready."
    )