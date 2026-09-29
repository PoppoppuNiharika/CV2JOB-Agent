from typing import Any
import math


class GapAnalyzer:
    """
    Analyze integrated CV-to-job matching results and identify
    meaningful skill gaps and evidence weaknesses.

    This layer does not decide whether a candidate should be
    hired. It identifies:
    - confirmed matches
    - evidence-supported requirements
    - potential matches
    - actual gaps
    - recommended next actions
    """

    VALID_STATUSES = {
        "Confirmed Match",
        "Evidence Match",
        "Evidence Found",
        "Potential Match",
        "Gap",
    }

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def analyze(
        self,
        integrated_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert integrated matching output into a structured
        gap analysis.
        """

        # -----------------------------------------------------
        # Validation
        # -----------------------------------------------------

        if not isinstance(
            integrated_result,
            dict,
        ):

            raise TypeError(
                "Integrated matching result must be "
                "a dictionary."
            )

        if not integrated_result:

            raise ValueError(
                "Integrated matching result is empty."
            )

        requirements = integrated_result.get(
            "requirements",
            [],
        )

        if not isinstance(
            requirements,
            list,
        ):

            raise TypeError(
                "Integrated result requirements must "
                "be a list."
            )

        gaps = []
        evidence_improvements = []

        # -----------------------------------------------------
        # Analyze every requirement
        # -----------------------------------------------------

        for requirement in requirements:

            if not isinstance(
                requirement,
                dict,
            ):

                raise TypeError(
                    "Every requirement result must "
                    "be a dictionary."
                )

            requirement_name = self._clean_text(
                requirement.get(
                    "requirement",
                    "",
                )
            )

            if not requirement_name:

                raise ValueError(
                    "Requirement name cannot be empty."
                )

            status = self._clean_text(
                requirement.get(
                    "status",
                    "",
                )
            )

            if status not in self.VALID_STATUSES:

                raise ValueError(
                    f"Unknown integrated match status: "
                    f"{status!r}"
                )

            category = self._get_category(
                requirement,
                integrated_result,
            )

            # -------------------------------------------------
            # Confirmed Match
            # -------------------------------------------------

            if status == "Confirmed Match":

                continue

            # -------------------------------------------------
            # Evidence Match
            # -------------------------------------------------

            if status == "Evidence Match":

                evidence_improvements.append(
                    self._create_evidence_improvement(
                        requirement=requirement_name,
                        category=category,
                        improvement_type=(
                            "Strengthen Evidence"
                        ),
                        priority=(
                            self._evidence_priority(
                                category
                            )
                        ),
                        reason=(
                            "The CV contains relevant evidence "
                            "and semantic support, but the "
                            "requirement is not an exact "
                            "skill-list match."
                        ),
                    )
                )

                continue

            # -------------------------------------------------
            # Evidence Found
            # -------------------------------------------------

            if status == "Evidence Found":

                evidence_improvements.append(
                    self._create_evidence_improvement(
                        requirement=requirement_name,
                        category=category,
                        improvement_type=(
                            "Strengthen Evidence"
                        ),
                        priority=(
                            self._evidence_priority(
                                category
                            )
                        ),
                        reason=(
                            "The CV contains explicit evidence "
                            "for the requirement, but the "
                            "semantic support is limited. "
                            "Making the evidence more specific "
                            "can improve clarity."
                        ),
                    )
                )

                continue

            # -------------------------------------------------
            # Potential Match
            # -------------------------------------------------

            if status == "Potential Match":

                evidence_improvements.append(
                    self._create_evidence_improvement(
                        requirement=requirement_name,
                        category=category,
                        improvement_type="Add Evidence",
                        priority="Medium",
                        reason=(
                            "The CV contains semantically "
                            "related content, but stronger "
                            "explicit evidence is needed "
                            "to support the requirement."
                        ),
                    )
                )

                continue

            # -------------------------------------------------
            # Gap
            # -------------------------------------------------

            if status == "Gap":

                gap = {
                    "requirement": requirement_name,
                    "category": category,
                    "priority": self._calculate_gap_priority(
                        category
                    ),
                    "reason": self._gap_reason(
                        requirement
                    ),
                    "suggested_action": (
                        self._suggest_action(
                            requirement_name,
                            category,
                        )
                    ),
                }

                gaps.append(
                    gap
                )

        # -----------------------------------------------------
        # Remove duplicates
        # -----------------------------------------------------

        gaps = self._deduplicate_records(
            gaps
        )

        evidence_improvements = (
            self._deduplicate_records(
                evidence_improvements
            )
        )

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        summary = {
            "total_gaps": len(
                gaps
            ),
            "high_priority_gaps": sum(
                1
                for gap in gaps
                if gap["priority"] == "High"
            ),
            "medium_priority_gaps": sum(
                1
                for gap in gaps
                if gap["priority"] == "Medium"
            ),
            "low_priority_gaps": sum(
                1
                for gap in gaps
                if gap["priority"] == "Low"
            ),
            "evidence_improvements": len(
                evidence_improvements
            ),
        }

        return {
            "job_title": self._clean_text(
                integrated_result.get(
                    "job_title",
                    "",
                )
            ),
            "gaps": gaps,
            "evidence_improvements": (
                evidence_improvements
            ),
            "summary": summary,
        }

    # =========================================================
    # CATEGORY
    # =========================================================

    def _get_category(
        self,
        requirement: dict[str, Any],
        integrated_result: dict[str, Any],
    ) -> str:
        """
        Get the requirement category.

        The integrated requirement's own category is preferred
        because it was assigned directly from the analyzed JD.

        The basic matcher is retained as a compatibility
        fallback for older result structures.
        """

        direct_category = self._clean_text(
            requirement.get(
                "category",
                "",
            )
        )

        if direct_category in {
            "Required Skill",
            "Preferred Skill",
            "Soft Skill",
        }:

            return direct_category

        return self._infer_category_from_basic_match(
            requirement.get(
                "requirement",
                "",
            ),
            integrated_result,
        )

    # =========================================================
    # CATEGORY FALLBACK
    # =========================================================

    def _infer_category_from_basic_match(
        self,
        requirement: str,
        integrated_result: dict[str, Any],
    ) -> str:
        """
        Infer category from basic_match for backward compatibility.
        """

        basic_match = integrated_result.get(
            "basic_match",
            {},
        )

        if not isinstance(
            basic_match,
            dict,
        ):

            return "Other"

        target = self._normalize(
            requirement
        )

        categories = [
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
        ]

        for key, category_name in categories:

            category_data = basic_match.get(
                key,
                {},
            )

            if not isinstance(
                category_data,
                dict,
            ):
                continue

            for list_name in (
                "matched",
                "missing",
            ):

                values = category_data.get(
                    list_name,
                    [],
                )

                if not isinstance(
                    values,
                    list,
                ):
                    continue

                for value in values:

                    if (
                        self._normalize(
                            value
                        )
                        == target
                    ):

                        return category_name

        return "Other"

    # =========================================================
    # GAP PRIORITY
    # =========================================================

    @staticmethod
    def _calculate_gap_priority(
        category: str,
    ) -> str:
        """
        Assign priority to an actual requirement gap.

        Required skills receive the highest priority.
        """

        if category == "Required Skill":

            return "High"

        if category == "Preferred Skill":

            return "Medium"

        if category == "Soft Skill":

            return "Medium"

        return "Low"

    # =========================================================
    # EVIDENCE IMPROVEMENT PRIORITY
    # =========================================================

    @staticmethod
    def _evidence_priority(
        category: str,
    ) -> str:
        """
        Assign priority to an evidence weakness.

        Evidence improvements are less urgent than actual
        missing skills, but required-skill evidence can still
        be important.
        """

        if category == "Required Skill":

            return "Medium"

        return "Low"

    # =========================================================
    # CREATE EVIDENCE IMPROVEMENT
    # =========================================================

    @staticmethod
    def _create_evidence_improvement(
        requirement: str,
        category: str,
        improvement_type: str,
        priority: str,
        reason: str,
    ) -> dict[str, Any]:
        """
        Create a standardized evidence-improvement record.
        """

        return {
            "requirement": requirement,
            "category": category,
            "type": improvement_type,
            "priority": priority,
            "reason": reason,
        }

    # =========================================================
    # GAP REASON
    # =========================================================

    @staticmethod
    def _gap_reason(
        requirement: dict[str, Any],
    ) -> str:
        """
        Explain why an integrated requirement is a gap.
        """

        evidence = requirement.get(
            "evidence",
            [],
        )

        semantic_score = (
            GapAnalyzer._safe_score(
                requirement.get(
                    "semantic_score",
                    0.0,
                )
            )
        )

        has_evidence = bool(
            evidence
        )

        if (
            not has_evidence
            and semantic_score < 0.50
        ):

            return (
                "No explicit CV evidence was found and "
                "semantic similarity is low."
            )

        if not has_evidence:

            return (
                "No explicit CV evidence was found."
            )

        return (
            "Some related information exists, but it "
            "does not provide sufficient evidence."
        )

    # =========================================================
    # SUGGESTED ACTION
    # =========================================================

    @staticmethod
    def _suggest_action(
        requirement: str,
        category: str,
    ) -> str:
        """
        Generate a practical action for an actual gap.
        """

        if category == "Required Skill":

            return (
                f"Learn {requirement}, practice it through "
                "a small project, and add concrete evidence "
                "to the CV."
            )

        if category == "Preferred Skill":

            return (
                f"Consider learning {requirement} and "
                "demonstrating it through a relevant project."
            )

        if category == "Soft Skill":

            return (
                f"Add concrete project or experience evidence "
                f"that demonstrates {requirement}."
            )

        return (
            f"Review the requirement '{requirement}' and "
            "add relevant evidence if applicable."
        )

    # =========================================================
    # DEDUPLICATE RECORDS
    # =========================================================

    @classmethod
    def _deduplicate_records(
        cls,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Remove duplicate records by requirement and type.
        """

        unique = []

        seen = set()

        for record in records:

            key = (
                cls._normalize(
                    record.get(
                        "requirement",
                        "",
                    )
                ),
                cls._normalize(
                    record.get(
                        "type",
                        "",
                    )
                ),
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            unique.append(
                record
            )

        return unique

    # =========================================================
    # SAFE SCORE
    # =========================================================

    @staticmethod
    def _safe_score(
        value: Any,
    ) -> float:
        """
        Convert semantic score into a safe range.
        """

        try:

            score = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

        if not math.isfinite(
            score
        ):

            return 0.0

        return max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(
        value: Any,
    ) -> str:
        """
        Normalize text for comparison.
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
        Clean whitespace from text.
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
        "GapAnalyzer is ready."
    )