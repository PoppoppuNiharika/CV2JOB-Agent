from typing import Any
import math

from matcher import CVJobMatcher
from evidence_mapper import EvidenceMapper
from semantic_matcher import SemanticMatcher


class IntegratedMatcher:
    """
    Combine deterministic matching, explicit CV evidence,
    and semantic similarity into one final matching layer.

    Matching layers:

    1. Exact skill matching
    2. Explicit CV evidence
    3. Semantic similarity

    Important design rule:

    Semantic similarity alone does not prove that a candidate
    possesses a skill. It can indicate a potential relationship,
    but explicit evidence and deterministic matching have higher
    authority.

    This class preserves the output structure expected by
    downstream components such as GapAnalyzer and
    ReportGenerator.
    """

    # =========================================================
    # SEMANTIC THRESHOLDS
    # =========================================================

    STRONG_SEMANTIC_THRESHOLD = 0.70
    RELATED_SEMANTIC_THRESHOLD = 0.50

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        semantic_model_name: str = "all-MiniLM-L6-v2",
        semantic_matcher: Any | None = None,
    ):
        """
        Initialize the integrated matcher.

        Args:
            semantic_model_name:
                Sentence-transformer model name.

            semantic_matcher:
                Optional injected semantic matcher.

                This is useful for unit testing because it
                allows the decision logic to be tested without
                repeatedly loading an embedding model.
        """

        if not isinstance(
            semantic_model_name,
            str,
        ) or not semantic_model_name.strip():

            raise ValueError(
                "semantic_model_name must be a "
                "non-empty string."
            )

        self.semantic_model_name = (
            semantic_model_name.strip()
        )

        self.basic_matcher = CVJobMatcher()

        self.evidence_mapper = EvidenceMapper()

        if semantic_matcher is not None:

            if not hasattr(
                semantic_matcher,
                "compare",
            ):

                raise TypeError(
                    "semantic_matcher must provide "
                    "a compare() method."
                )

            self.semantic_matcher = semantic_matcher

        else:

            self.semantic_matcher = SemanticMatcher(
                model_name=self.semantic_model_name
            )

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def analyze(
        self,
        cv_profile: dict[str, Any],
        job_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Perform complete integrated CV-to-job analysis.

        Args:
            cv_profile:
                Structured CV profile.

            job_profile:
                Structured job profile.

        Returns:
            Integrated matching result containing:
            - final requirement analysis
            - summary
            - deterministic matching result
            - evidence mapping result
        """

        # -----------------------------------------------------
        # Input validation
        # -----------------------------------------------------

        if not isinstance(
            cv_profile,
            dict,
        ):

            raise TypeError(
                "CV profile must be a dictionary."
            )

        if not cv_profile:

            raise ValueError(
                "CV profile is empty."
            )

        if not isinstance(
            job_profile,
            dict,
        ):

            raise TypeError(
                "Job profile must be a dictionary."
            )

        if not job_profile:

            raise ValueError(
                "Job profile is empty."
            )

        # -----------------------------------------------------
        # 1. Deterministic matching
        # -----------------------------------------------------

        basic_result = self.basic_matcher.match(
            cv_profile,
            job_profile,
        )

        # -----------------------------------------------------
        # 2. Explicit evidence mapping
        # -----------------------------------------------------

        evidence_result = (
            self.evidence_mapper.map_evidence(
                cv_profile,
                job_profile,
            )
        )

        # -----------------------------------------------------
        # 3. Build CV semantic evidence
        # -----------------------------------------------------

        semantic_evidence = (
            self._build_semantic_evidence(
                cv_profile
            )
        )

        # -----------------------------------------------------
        # 4. Collect unique job requirements
        # -----------------------------------------------------

        requirements = (
            self._collect_requirements(
                job_profile
            )
        )

        # -----------------------------------------------------
        # 5. Semantic comparison
        # -----------------------------------------------------

        semantic_results = (
            self.semantic_matcher.compare(
                requirements,
                semantic_evidence,
            )
        )

        # -----------------------------------------------------
        # Validate semantic result coverage
        # -----------------------------------------------------

        semantic_by_requirement = {
            self._normalize_requirement(
                result.get(
                    "requirement",
                    "",
                )
            ): result
            for result in semantic_results
            if isinstance(
                result,
                dict,
            )
        }

        # -----------------------------------------------------
        # 6. Combine all signals
        # -----------------------------------------------------

        final_requirements = []

        for requirement in requirements:

            normalized_requirement = (
                self._normalize_requirement(
                    requirement
                )
            )

            semantic_result = (
                semantic_by_requirement.get(
                    normalized_requirement,
                    {
                        "requirement": requirement,
                        "best_evidence": "",
                        "similarity_score": 0.0,
                        "match_level": "No Evidence",
                    },
                )
            )

            evidence_item = (
                self._find_evidence_result(
                    requirement,
                    evidence_result,
                )
            )

            basic_status = (
                self._find_basic_status(
                    requirement,
                    basic_result,
                )
            )

            category = (
                self._find_requirement_category(
                    requirement,
                    job_profile,
                )
            )

            final_result = (
                self._combine_results(
                    requirement=requirement,
                    category=category,
                    evidence_result=evidence_item,
                    basic_status=basic_status,
                    semantic_result=semantic_result,
                )
            )

            final_requirements.append(
                final_result
            )

        # -----------------------------------------------------
        # 7. Summary
        # -----------------------------------------------------

        summary = self._create_summary(
            final_requirements
        )

        return {
            "job_title": self._clean_text(
                job_profile.get(
                    "job_title",
                    "",
                )
            ),
            "requirements": final_requirements,
            "summary": summary,
            "basic_match": basic_result,
            "evidence_mapping": evidence_result,
        }

    # =========================================================
    # BUILD SEMANTIC EVIDENCE
    # =========================================================

    def _build_semantic_evidence(
        self,
        cv_profile: dict[str, Any],
    ) -> list[str]:
        """
        Build meaningful CV evidence for semantic comparison.

        Priority is given to:
        - summary
        - experience
        - projects
        - certifications
        - activities
        - technical skills

        The method does not use raw CV text directly because
        that can introduce duplicated and noisy information.
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
        ):

            cleaned = self._clean_text(
                summary
            )

            if cleaned:
                evidence.append(
                    cleaned
                )

        # -----------------------------------------------------
        # Experience
        # -----------------------------------------------------

        self._collect_structured_text(
            cv_profile.get(
                "experience",
                [],
            ),
            evidence,
        )

        # -----------------------------------------------------
        # Projects
        # -----------------------------------------------------

        self._collect_structured_text(
            cv_profile.get(
                "projects",
                [],
            ),
            evidence,
        )

        # -----------------------------------------------------
        # Certifications
        # -----------------------------------------------------

        self._collect_structured_text(
            cv_profile.get(
                "certifications",
                [],
            ),
            evidence,
        )

        # -----------------------------------------------------
        # Activities
        # -----------------------------------------------------

        self._collect_structured_text(
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

                    if not isinstance(
                        value,
                        str,
                    ):
                        continue

                    cleaned = self._clean_text(
                        value
                    )

                    if not cleaned:
                        continue

                    evidence.append(
                        f"{category}: {cleaned}"
                    )

        return self._clean_evidence(
            evidence
        )

    # =========================================================
    # COLLECT STRUCTURED TEXT
    # =========================================================

    def _collect_structured_text(
        self,
        items: Any,
        evidence: list[str],
    ) -> None:
        """
        Extract meaningful text from structured CV sections.
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

                cleaned = self._clean_text(
                    item
                )

                if cleaned:
                    evidence.append(
                        cleaned
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

                    cleaned = self._clean_text(
                        value
                    )

                    if cleaned:
                        evidence.append(
                            cleaned
                        )

                elif isinstance(
                    value,
                    list,
                ):

                    for nested in value:

                        if not isinstance(
                            nested,
                            str,
                        ):
                            continue

                        cleaned = self._clean_text(
                            nested
                        )

                        if cleaned:
                            evidence.append(
                                cleaned
                            )

    # =========================================================
    # COLLECT REQUIREMENTS
    # =========================================================

    @classmethod
    def _collect_requirements(
        cls,
        job_profile: dict[str, Any],
    ) -> list[str]:
        """
        Collect unique job requirements while preserving
        their original order.
        """

        requirements = []

        seen = set()

        for category in (
            "required_skills",
            "preferred_skills",
            "soft_skills",
        ):

            values = job_profile.get(
                category,
                [],
            )

            if not isinstance(
                values,
                list,
            ):
                continue

            for requirement in values:

                if not isinstance(
                    requirement,
                    str,
                ):
                    continue

                cleaned = cls._clean_text(
                    requirement
                )

                normalized = cls._normalize_requirement(
                    cleaned
                )

                if not normalized:
                    continue

                if normalized in seen:
                    continue

                seen.add(
                    normalized
                )

                requirements.append(
                    cleaned
                )

        return requirements

    # =========================================================
    # FIND EVIDENCE RESULT
    # =========================================================

    @classmethod
    def _find_evidence_result(
        cls,
        requirement: str,
        evidence_result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Find the deterministic evidence record for a requirement.
        """

        if not isinstance(
            evidence_result,
            dict,
        ):
            return None

        requirements = evidence_result.get(
            "requirements",
            [],
        )

        if not isinstance(
            requirements,
            list,
        ):
            return None

        target = cls._normalize_requirement(
            requirement
        )

        for item in requirements:

            if not isinstance(
                item,
                dict,
            ):
                continue

            candidate = cls._normalize_requirement(
                item.get(
                    "requirement",
                    "",
                )
            )

            if candidate == target:

                return item

        return None

    # =========================================================
    # FIND BASIC STATUS
    # =========================================================

    @classmethod
    def _find_basic_status(
        cls,
        requirement: str,
        basic_result: dict[str, Any],
    ) -> str:
        """
        Determine whether the deterministic matcher found
        an exact skill match.
        """

        if not isinstance(
            basic_result,
            dict,
        ):
            return "Not Exact Match"

        target = cls._normalize_requirement(
            requirement
        )

        for category in (
            "required_skills",
            "preferred_skills",
            "soft_skills",
        ):

            category_result = basic_result.get(
                category,
                {},
            )

            if not isinstance(
                category_result,
                dict,
            ):
                continue

            matched = category_result.get(
                "matched",
                [],
            )

            if not isinstance(
                matched,
                list,
            ):
                continue

            for skill in matched:

                if (
                    cls._normalize_requirement(
                        skill
                    )
                    == target
                ):

                    return "Exact Match"

        return "Not Exact Match"

    # =========================================================
    # FIND REQUIREMENT CATEGORY
    # =========================================================

    @classmethod
    def _find_requirement_category(
        cls,
        requirement: str,
        job_profile: dict[str, Any],
    ) -> str:
        """
        Determine the original requirement category.
        """

        target = cls._normalize_requirement(
            requirement
        )

        category_map = (
            (
                "required_skills",
                "Required Skill",
            ),
            (
                "preferred_skills",
                "Preferred Skill",
            ),
            (
                "soft_skills",
                "Soft Skill",
            ),
        )

        for key, label in category_map:

            values = job_profile.get(
                key,
                [],
            )

            if not isinstance(
                values,
                list,
            ):
                continue

            for value in values:

                if (
                    cls._normalize_requirement(
                        value
                    )
                    == target
                ):

                    return label

        return "Other"

    # =========================================================
    # COMBINE RESULTS
    # =========================================================

    def _combine_results(
        self,
        requirement: str,
        category: str,
        evidence_result: dict[str, Any] | None,
        basic_status: str,
        semantic_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Combine deterministic matching, explicit evidence,
        and semantic similarity.

        Decision hierarchy:

        1. Exact Match
           -> Confirmed Match

        2. Explicit evidence + related/strong semantics
           -> Evidence Match

        3. Explicit evidence + weak semantics
           -> Evidence Found

        4. No explicit evidence + strong semantics
           -> Potential Match

        5. Otherwise
           -> Gap

        Semantic similarity alone never becomes a confirmed
        or evidence match.
        """

        explicit_evidence = bool(
            evidence_result
            and evidence_result.get(
                "evidence",
                [],
            )
        )

        raw_score = (
            semantic_result.get(
                "similarity_score",
                0.0,
            )
            if isinstance(
                semantic_result,
                dict,
            )
            else 0.0
        )

        semantic_score = self._safe_score(
            raw_score
        )

        semantic_level = (
            semantic_result.get(
                "match_level",
                "No Meaningful Evidence",
            )
            if isinstance(
                semantic_result,
                dict,
            )
            else "No Meaningful Evidence"
        )

        if not isinstance(
            semantic_level,
            str,
        ):
            semantic_level = (
                "No Meaningful Evidence"
            )

        # -----------------------------------------------------
        # Final status
        # -----------------------------------------------------

        if basic_status == "Exact Match":

            final_status = "Confirmed Match"

        elif explicit_evidence:

            if (
                semantic_score
                >= self.RELATED_SEMANTIC_THRESHOLD
            ):

                final_status = "Evidence Match"

            else:

                final_status = "Evidence Found"

        elif (
            semantic_score
            >= self.STRONG_SEMANTIC_THRESHOLD
        ):

            final_status = "Potential Match"

        else:

            final_status = "Gap"

        # -----------------------------------------------------
        # Confidence
        # -----------------------------------------------------

        confidence = self._calculate_confidence(
            basic_status=basic_status,
            explicit_evidence=explicit_evidence,
            semantic_score=semantic_score,
        )

        return {
            "requirement": requirement,
            "category": category,
            "status": final_status,
            "confidence": confidence,
            "basic_match": basic_status,
            "semantic_score": semantic_score,
            "semantic_level": semantic_level,
            "evidence": (
                evidence_result.get(
                    "evidence",
                    [],
                )
                if evidence_result
                else []
            ),
            "best_semantic_evidence": (
                semantic_result.get(
                    "best_evidence",
                    "",
                )
                if isinstance(
                    semantic_result,
                    dict,
                )
                else ""
            ),
        }

    # =========================================================
    # CONFIDENCE
    # =========================================================

    @staticmethod
    def _calculate_confidence(
        basic_status: str,
        explicit_evidence: bool,
        semantic_score: float,
    ) -> str:
        """
        Calculate an interpretable confidence level.
        """

        if basic_status == "Exact Match":

            return "High"

        if explicit_evidence:

            if semantic_score >= 0.60:

                return "High"

            return "Medium"

        if semantic_score >= 0.70:

            return "Medium"

        return "Low"

    # =========================================================
    # SUMMARY
    # =========================================================

    @staticmethod
    def _create_summary(
        requirements: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Summarize integrated matching results.

        confirmed_matches:
            Exact deterministic matches only.

        evidence_matches:
            Explicit CV evidence supported by semantic
            relatedness.

        potential_matches:
            Strong semantic similarity without explicit
            evidence.

        gaps:
            No sufficient supporting signal.
        """

        confirmed_matches = sum(
            1
            for item in requirements
            if item.get(
                "status"
            ) == "Confirmed Match"
        )

        evidence_matches = sum(
            1
            for item in requirements
            if item.get(
                "status"
            ) == "Evidence Match"
        )

        evidence_found = sum(
            1
            for item in requirements
            if item.get(
                "evidence"
            )
        )

        potential_matches = sum(
            1
            for item in requirements
            if item.get(
                "status"
            ) == "Potential Match"
        )

        gaps = sum(
            1
            for item in requirements
            if item.get(
                "status"
            ) == "Gap"
        )

        total = len(
            requirements
        )

        resolved_matches = (
            confirmed_matches
            + evidence_matches
        )

        if total:

            coverage_percentage = round(
                (
                    (
                        resolved_matches
                        + potential_matches
                    )
                    / total
                )
                * 100,
                2,
            )

        else:

            coverage_percentage = 0.0

        return {
            "total_requirements": total,
            "confirmed_matches": confirmed_matches,
            "evidence_matches": evidence_matches,
            "potential_matches": potential_matches,
            "evidence_found": evidence_found,
            "gaps": gaps,
            "resolved_matches": resolved_matches,
            "coverage_percentage": coverage_percentage,
        }

    # =========================================================
    # CLEAN EVIDENCE
    # =========================================================

    @staticmethod
    def _clean_evidence(
        evidence: list[str],
    ) -> list[str]:
        """
        Remove duplicate and empty semantic evidence.
        """

        cleaned = []

        seen = set()

        for item in evidence:

            if not isinstance(
                item,
                str,
            ):
                continue

            normalized = (
                " ".join(
                    item.split()
                ).strip()
            )

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
    # SCORE VALIDATION
    # =========================================================

    @staticmethod
    def _safe_score(
        score: Any,
    ) -> float:
        """
        Convert a similarity score into a safe bounded float.
        """

        try:

            numeric_score = float(
                score
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        if not math.isfinite(
            numeric_score
        ):

            return 0.0

        return max(
            0.0,
            min(
                1.0,
                numeric_score,
            ),
        )

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_requirement(
        value: Any,
    ) -> str:
        """
        Normalize requirement names for comparison.
        """

        if not isinstance(
            value,
            str,
        ):
            return ""

        return (
            " ".join(
                value.strip().lower().split()
            )
        )

    # =========================================================
    # TEXT CLEANING
    # =========================================================

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        """
        Normalize whitespace in text.
        """

        if not isinstance(
            value,
            str,
        ):
            return ""

        return (
            " ".join(
                value.split()
            ).strip()
        )


if __name__ == "__main__":

    print(
        "IntegratedMatcher is ready."
    )