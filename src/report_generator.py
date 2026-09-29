from typing import Any


class ReportGenerator:
    """
    Combine the outputs of the matching, gap-analysis, and
    improvement-planning layers into one final report.

    This class is intentionally an aggregation layer.

    It does not:
        - invent candidate information
        - perform new skill matching
        - recalculate semantic similarity
        - change matcher decisions

    It simply validates and organizes the outputs of the
    previous pipeline stages into a stable report schema.
    """

    # =========================================================
    # CONSTANTS
    # =========================================================

    VALID_MATCH_STATUSES = {
        "Confirmed Match",
        "Evidence Match",
        "Evidence Found",
        "Potential Match",
        "Gap",
    }

    VALID_PRIORITIES = {
        "High",
        "Medium",
        "Low",
    }

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def generate(
        self,
        integrated_result: dict[str, Any],
        gap_analysis: dict[str, Any],
        improvement_plan: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate the final CV-to-job analysis report.

        Args:
            integrated_result:
                Output from IntegratedMatcher.

            gap_analysis:
                Output from GapAnalyzer.

            improvement_plan:
                Output from ImprovementPlanner.

        Returns:
            A structured final report suitable for:
                - Streamlit UI
                - JSON serialization
                - downstream APIs
                - report generation
                - testing
        """

        # -----------------------------------------------------
        # Validate top-level inputs
        # -----------------------------------------------------

        self._validate_input(
            integrated_result,
            "integrated_result",
        )

        self._validate_input(
            gap_analysis,
            "gap_analysis",
        )

        self._validate_input(
            improvement_plan,
            "improvement_plan",
        )

        # -----------------------------------------------------
        # Extract matcher information
        # -----------------------------------------------------

        matcher_summary = integrated_result.get(
            "summary",
            {},
        )

        basic_match = integrated_result.get(
            "basic_match",
            {},
        )

        if not isinstance(
            matcher_summary,
            dict,
        ):
            raise TypeError(
                "Integrated matcher summary must be a dictionary."
            )

        if not isinstance(
            basic_match,
            dict,
        ):
            raise TypeError(
                "Basic match result must be a dictionary."
            )

        # -----------------------------------------------------
        # Extract overall deterministic match
        #
        # This is the score produced by CVJobMatcher.
        # It is kept separate from requirement coverage.
        # -----------------------------------------------------

        overall_match = self._get_numeric_value(
            basic_match.get(
                "overall_match_percentage",
                0.0,
            ),
            "overall_match_percentage",
        )

        # -----------------------------------------------------
        # Extract integrated requirement coverage
        # -----------------------------------------------------

        coverage = self._get_numeric_value(
            matcher_summary.get(
                "coverage_percentage",
                0.0,
            ),
            "coverage_percentage",
        )

        # -----------------------------------------------------
        # Extract requirement list
        # -----------------------------------------------------

        requirements = integrated_result.get(
            "requirements",
            [],
        )

        self._validate_list(
            requirements,
            "requirements",
        )

        self._validate_requirement_records(
            requirements,
        )

        # -----------------------------------------------------
        # Extract gap-analysis information
        # -----------------------------------------------------

        gaps = gap_analysis.get(
            "gaps",
            [],
        )

        evidence_improvements = gap_analysis.get(
            "evidence_improvements",
            [],
        )

        self._validate_list(
            gaps,
            "gaps",
        )

        self._validate_list(
            evidence_improvements,
            "evidence_improvements",
        )

        self._validate_gap_records(
            gaps,
        )

        self._validate_gap_records(
            evidence_improvements,
        )

        # -----------------------------------------------------
        # Extract improvement-plan information
        # -----------------------------------------------------

        action_plan = improvement_plan.get(
            "action_plan",
            [],
        )

        improvement_summary = improvement_plan.get(
            "summary",
            {},
        )

        self._validate_list(
            action_plan,
            "action_plan",
        )

        if not isinstance(
            improvement_summary,
            dict,
        ):
            raise TypeError(
                "Improvement plan summary must be a dictionary."
            )

        self._validate_action_records(
            action_plan,
        )

        # -----------------------------------------------------
        # Build final report
        # -----------------------------------------------------

        return {
            "job_title": self._clean_string(
                integrated_result.get(
                    "job_title",
                    "",
                )
            ),

            "overall_match": overall_match,

            "coverage": coverage,

            "match_summary": self._build_match_summary(
                matcher_summary
            ),

            "requirements": requirements,

            "gaps": gaps,

            "evidence_improvements": (
                evidence_improvements
            ),

            "improvement_plan": action_plan,

            "improvement_summary": improvement_summary,
        }

    # =========================================================
    # MATCH SUMMARY
    # =========================================================

    @classmethod
    def _build_match_summary(
        cls,
        matcher_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build a complete and stable match-summary structure.

        Newer matcher fields are included while preserving the
        existing fields used by earlier code.
        """

        return {
            "total_requirements": cls._safe_count(
                matcher_summary.get(
                    "total_requirements",
                    0,
                )
            ),

            "confirmed_matches": cls._safe_count(
                matcher_summary.get(
                    "confirmed_matches",
                    0,
                )
            ),

            "evidence_matches": cls._safe_count(
                matcher_summary.get(
                    "evidence_matches",
                    0,
                )
            ),

            "potential_matches": cls._safe_count(
                matcher_summary.get(
                    "potential_matches",
                    0,
                )
            ),

            "evidence_found": cls._safe_count(
                matcher_summary.get(
                    "evidence_found",
                    0,
                )
            ),

            "gaps": cls._safe_count(
                matcher_summary.get(
                    "gaps",
                    0,
                )
            ),

            "resolved_matches": cls._safe_count(
                matcher_summary.get(
                    "resolved_matches",
                    0,
                )
            ),

            "coverage_percentage": cls._safe_percentage(
                matcher_summary.get(
                    "coverage_percentage",
                    0.0,
                )
            ),
        }

    # =========================================================
    # VALIDATION HELPERS
    # =========================================================

    @staticmethod
    def _validate_input(
        value: Any,
        name: str,
    ) -> None:
        """
        Validate a required top-level dictionary.
        """

        if not isinstance(
            value,
            dict,
        ):
            raise TypeError(
                f"{name} must be a dictionary."
            )

        if not value:
            raise ValueError(
                f"{name} is empty."
            )

    @staticmethod
    def _validate_list(
        value: Any,
        name: str,
    ) -> None:
        """
        Validate a list field.
        """

        if not isinstance(
            value,
            list,
        ):
            raise TypeError(
                f"{name} must be a list."
            )

    @classmethod
    def _validate_requirement_records(
        cls,
        requirements: list[Any],
    ) -> None:
        """
        Validate integrated matcher requirement records.
        """

        for index, requirement in enumerate(
            requirements
        ):

            if not isinstance(
                requirement,
                dict,
            ):
                raise TypeError(
                    f"requirements[{index}] must be a dictionary."
                )

            if "requirement" not in requirement:
                raise ValueError(
                    f"requirements[{index}] is missing "
                    "'requirement'."
                )

            requirement_name = requirement.get(
                "requirement"
            )

            if not isinstance(
                requirement_name,
                str,
            ) or not requirement_name.strip():

                raise ValueError(
                    f"requirements[{index}] must contain "
                    "a non-empty requirement name."
                )

            # Status is optional for backward compatibility.
            status = requirement.get(
                "status"
            )

            if status is not None:
                if status not in cls.VALID_MATCH_STATUSES:
                    raise ValueError(
                        f"requirements[{index}] has invalid "
                        f"status: {status!r}."
                    )

    @classmethod
    def _validate_gap_records(
        cls,
        records: list[Any],
    ) -> None:
        """
        Validate gap/evidence-improvement records.
        """

        for index, record in enumerate(
            records
        ):

            if not isinstance(
                record,
                dict,
            ):
                raise TypeError(
                    f"Gap record {index} must be a dictionary."
                )

            if "requirement" not in record:
                raise ValueError(
                    f"Gap record {index} is missing "
                    "'requirement'."
                )

            requirement = record.get(
                "requirement"
            )

            if not isinstance(
                requirement,
                str,
            ) or not requirement.strip():

                raise ValueError(
                    f"Gap record {index} must contain "
                    "a non-empty requirement."
                )

            priority = record.get(
                "priority"
            )

            if priority is not None:
                if priority not in cls.VALID_PRIORITIES:
                    raise ValueError(
                        f"Gap record {index} has invalid "
                        f"priority: {priority!r}."
                    )

    @classmethod
    def _validate_action_records(
        cls,
        actions: list[Any],
    ) -> None:
        """
        Validate improvement-plan action records.
        """

        for index, action in enumerate(
            actions
        ):

            if not isinstance(
                action,
                dict,
            ):
                raise TypeError(
                    f"action_plan[{index}] must be a dictionary."
                )

            requirement = action.get(
                "requirement"
            )

            if not isinstance(
                requirement,
                str,
            ) or not requirement.strip():

                raise ValueError(
                    f"action_plan[{index}] must contain "
                    "a non-empty requirement."
                )

            priority = action.get(
                "priority"
            )

            if priority is not None:
                if priority not in cls.VALID_PRIORITIES:
                    raise ValueError(
                        f"action_plan[{index}] has invalid "
                        f"priority: {priority!r}."
                    )

            steps = action.get(
                "steps"
            )

            if steps is not None:
                if not isinstance(
                    steps,
                    list,
                ):
                    raise TypeError(
                        f"action_plan[{index}]['steps'] "
                        "must be a list."
                    )

                for step_index, step in enumerate(
                    steps
                ):
                    if not isinstance(
                        step,
                        str,
                    ):
                        raise TypeError(
                            f"action_plan[{index}]['steps']"
                            f"[{step_index}] must be a string."
                        )

    # =========================================================
    # VALUE HELPERS
    # =========================================================

    @staticmethod
    def _clean_string(
        value: Any,
    ) -> str:
        """
        Normalize an optional string value.
        """

        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "String field must contain a string."
            )

        return " ".join(
            value.split()
        )

    @staticmethod
    def _get_numeric_value(
        value: Any,
        name: str,
    ) -> float:
        """
        Validate and normalize a numeric metric.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be numeric."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{name} must be numeric."
            )

        numeric_value = float(
            value
        )

        if numeric_value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        if numeric_value > 100.0:
            raise ValueError(
                f"{name} cannot exceed 100."
            )

        return numeric_value

    @staticmethod
    def _safe_percentage(
        value: Any,
    ) -> float:
        """
        Normalize a percentage while validating its range.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "Percentage must be numeric."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "Percentage must be numeric."
            )

        percentage = float(
            value
        )

        if percentage < 0.0:
            raise ValueError(
                "Percentage cannot be negative."
            )

        if percentage > 100.0:
            raise ValueError(
                "Percentage cannot exceed 100."
            )

        return percentage

    @staticmethod
    def _safe_count(
        value: Any,
    ) -> int:
        """
        Validate a non-negative integer count.
        """

        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "Count must be an integer."
            )

        if not isinstance(
            value,
            int,
        ):
            raise TypeError(
                "Count must be an integer."
            )

        if value < 0:
            raise ValueError(
                "Count cannot be negative."
            )

        return value


if __name__ == "__main__":

    print(
        "ReportGenerator is ready."
    )