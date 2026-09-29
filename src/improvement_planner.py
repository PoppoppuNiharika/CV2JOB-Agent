from typing import Any


class ImprovementPlanner:
    """
    Convert gap-analysis results into a targeted improvement plan.

    The planner does not invent a candidate's skills, experience,
    projects, achievements, or outcomes.

    It only creates actions from:
        1. Actual requirement gaps.
        2. Evidence weaknesses identified by GapAnalyzer.

    The output is designed to be:
        - deterministic
        - validated
        - easy to display in the UI
        - compatible with ReportGenerator
        - useful for learning, projects, CV improvement, and interviews
    """

    VALID_PRIORITIES = {
        "High",
        "Medium",
        "Low",
    }

    VALID_CATEGORIES = {
        "Required Skill",
        "Preferred Skill",
        "Soft Skill",
        "Other",
    }

    PRIORITY_ORDER = {
        "High": 1,
        "Medium": 2,
        "Low": 3,
    }

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def create_plan(
        self,
        gap_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Create a personalized improvement plan.

        Args:
            gap_analysis:
                Output produced by GapAnalyzer.

        Returns:
            Structured improvement plan containing:
                - job_title
                - action_plan
                - summary
        """

        self._validate_gap_analysis(
            gap_analysis
        )

        gaps = gap_analysis.get(
            "gaps",
            [],
        )

        evidence_improvements = gap_analysis.get(
            "evidence_improvements",
            [],
        )

        self._validate_items(
            gaps,
            "gaps",
        )

        self._validate_items(
            evidence_improvements,
            "evidence_improvements",
        )

        action_plan: list[dict[str, Any]] = []

        seen_requirements: set[str] = set()

        # -----------------------------------------------------
        # 1. Create actions for actual gaps
        # -----------------------------------------------------

        for gap in gaps:

            requirement = self._clean_requirement(
                gap.get(
                    "requirement",
                    "",
                )
            )

            if not requirement:
                raise ValueError(
                    "Every gap must contain a non-empty requirement."
                )

            normalized_requirement = (
                requirement.casefold()
            )

            if normalized_requirement in seen_requirements:
                continue

            category = self._normalize_category(
                gap.get(
                    "category",
                    "Other",
                )
            )

            priority = self._normalize_priority(
                gap.get(
                    "priority",
                    "Low",
                )
            )

            action = self._create_gap_action(
                requirement=requirement,
                category=category,
                priority=priority,
            )

            action_plan.append(
                action
            )

            seen_requirements.add(
                normalized_requirement
            )

        # -----------------------------------------------------
        # 2. Create actions for evidence weaknesses
        # -----------------------------------------------------

        for improvement in evidence_improvements:

            requirement = self._clean_requirement(
                improvement.get(
                    "requirement",
                    "",
                )
            )

            if not requirement:
                raise ValueError(
                    "Every evidence improvement must contain "
                    "a non-empty requirement."
                )

            normalized_requirement = (
                requirement.casefold()
            )

            # An actual gap takes precedence over an
            # evidence-improvement action for the same requirement.
            if normalized_requirement in seen_requirements:
                continue

            category = self._normalize_category(
                improvement.get(
                    "category",
                    "Other",
                )
            )

            priority = self._normalize_priority(
                improvement.get(
                    "priority",
                    "Low",
                )
            )

            action = self._create_evidence_action(
                requirement=requirement,
                category=category,
                priority=priority,
            )

            action_plan.append(
                action
            )

            seen_requirements.add(
                normalized_requirement
            )

        # -----------------------------------------------------
        # 3. Sort by priority
        # -----------------------------------------------------

        action_plan.sort(
            key=lambda item: self.PRIORITY_ORDER.get(
                item.get(
                    "priority",
                    "Low",
                ),
                3,
            )
        )

        # -----------------------------------------------------
        # 4. Build summary
        # -----------------------------------------------------

        summary = self._build_summary(
            action_plan
        )

        job_title = gap_analysis.get(
            "job_title",
            "",
        )

        if job_title is None:
            job_title = ""

        if not isinstance(
            job_title,
            str,
        ):
            raise TypeError(
                "job_title must be a string."
            )

        return {
            "job_title": job_title.strip(),
            "action_plan": action_plan,
            "summary": summary,
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    @classmethod
    def _validate_gap_analysis(
        cls,
        gap_analysis: dict[str, Any],
    ) -> None:
        """
        Validate the top-level GapAnalyzer output.
        """

        if not isinstance(
            gap_analysis,
            dict,
        ):
            raise TypeError(
                "Gap analysis must be a dictionary."
            )

        if not gap_analysis:
            raise ValueError(
                "Gap analysis result is empty."
            )

    @staticmethod
    def _validate_items(
        items: Any,
        field_name: str,
    ) -> None:
        """
        Ensure a gap-analysis collection is a list of dictionaries.
        """

        if not isinstance(
            items,
            list,
        ):
            raise TypeError(
                f"'{field_name}' must be a list."
            )

        for index, item in enumerate(
            items
        ):

            if not isinstance(
                item,
                dict,
            ):
                raise TypeError(
                    f"'{field_name}[{index}]' must be a dictionary."
                )

    @classmethod
    def _normalize_priority(
        cls,
        priority: Any,
    ) -> str:
        """
        Normalize and validate action priority.
        """

        if priority is None:
            return "Low"

        if not isinstance(
            priority,
            str,
        ):
            raise TypeError(
                "Priority must be a string."
            )

        cleaned = priority.strip()

        if not cleaned:
            return "Low"

        normalized = cleaned.title()

        if normalized not in cls.VALID_PRIORITIES:
            raise ValueError(
                "Invalid priority. Expected one of: "
                "High, Medium, Low."
            )

        return normalized

    @classmethod
    def _normalize_category(
        cls,
        category: Any,
    ) -> str:
        """
        Normalize a requirement category.
        """

        if category is None:
            return "Other"

        if not isinstance(
            category,
            str,
        ):
            raise TypeError(
                "Category must be a string."
            )

        cleaned = " ".join(
            category.split()
        )

        if not cleaned:
            return "Other"

        if cleaned in cls.VALID_CATEGORIES:
            return cleaned

        return cleaned

    @staticmethod
    def _clean_requirement(
        requirement: Any,
    ) -> str:
        """
        Normalize requirement text without changing its meaning.
        """

        if requirement is None:
            return ""

        if not isinstance(
            requirement,
            str,
        ):
            raise TypeError(
                "Requirement must be a string."
            )

        return " ".join(
            requirement.split()
        )

    # =========================================================
    # GAP ACTION
    # =========================================================

    @classmethod
    def _create_gap_action(
        cls,
        requirement: str,
        category: str,
        priority: str,
    ) -> dict[str, Any]:
        """
        Create a practical action for a missing requirement.
        """

        if category == "Required Skill":

            steps = [
                (
                    f"Learn the core concepts and fundamentals "
                    f"of {requirement}."
                ),
                (
                    f"Practice {requirement} through small "
                    "hands-on exercises."
                ),
                (
                    f"Apply {requirement} in a relevant "
                    "mini-project or practical task."
                ),
                (
                    "Document the genuine work so it can be "
                    "demonstrated in the portfolio, CV, "
                    "and interview."
                ),
            ]

            action_type = "Skill Development"

            rationale = (
                f"{requirement} is a required job "
                "requirement that is currently identified "
                "as a gap."
            )

        elif category == "Preferred Skill":

            steps = [
                (
                    f"Learn the practical fundamentals "
                    f"of {requirement}."
                ),
                (
                    f"Complete a small hands-on task using "
                    f"{requirement}."
                ),
                (
                    f"Apply {requirement} to a relevant "
                    "existing project or practice project."
                ),
                (
                    "Add it to the CV only after there is "
                    "genuine evidence of using it."
                ),
            ]

            action_type = "Optional Skill Development"

            rationale = (
                f"{requirement} is a preferred requirement "
                "that is currently identified as a gap."
            )

        elif category == "Soft Skill":

            steps = [
                (
                    f"Identify a real project, internship, "
                    f"academic task, or activity where "
                    f"{requirement} was genuinely demonstrated."
                ),
                (
                    "Write down the situation, the action "
                    "taken, and the result using a simple "
                    "STAR-style structure."
                ),
                (
                    "Convert the real example into a concise "
                    "CV bullet and an interview-ready story."
                ),
            ]

            action_type = "Evidence Development"

            rationale = (
                f"{requirement} is a soft-skill requirement "
                "without sufficient current evidence."
            )

        else:

            steps = [
                (
                    f"Review the requirement "
                    f"{requirement} and determine what "
                    "it means for the target role."
                ),
                (
                    "Check whether relevant genuine "
                    "experience already exists."
                ),
                (
                    "Build or document genuine supporting "
                    "evidence before adding it to the CV."
                ),
            ]

            action_type = "Requirement Review"

            rationale = (
                f"{requirement} needs further review and "
                "supporting evidence."
            )

        return {
            "requirement": requirement,
            "category": category,
            "type": action_type,
            "priority": priority,
            "rationale": rationale,
            "steps": steps,
        }

    # =========================================================
    # EVIDENCE ACTION
    # =========================================================

    @staticmethod
    def _create_evidence_action(
        requirement: str,
        category: str,
        priority: str,
    ) -> dict[str, Any]:
        """
        Create an action for a requirement where evidence
        exists but should be made clearer or stronger.

        This method does not assume that the candidate needs
        to learn the skill again.
        """

        steps = [
            (
                f"Review the existing CV evidence for "
                f"{requirement}."
            ),
            (
                "Rewrite the relevant CV bullet so the "
                "actual task, tool, contribution, or result "
                "is easier to understand."
            ),
            (
                "Add measurable details only when they are "
                "supported by the candidate's real work."
            ),
            (
                "Verify the revised bullet against the "
                "original project or experience before "
                "using it in the final CV."
            ),
        ]

        rationale = (
            f"The pipeline found evidence related to "
            f"{requirement}, but the evidence should be "
            "presented more clearly or specifically."
        )

        return {
            "requirement": requirement,
            "category": category,
            "type": "Evidence Improvement",
            "priority": priority,
            "rationale": rationale,
            "steps": steps,
        }

    # =========================================================
    # SUMMARY
    # =========================================================

    @classmethod
    def _build_summary(
        cls,
        action_plan: list[dict[str, Any]],
    ) -> dict[str, int]:
        """
        Count improvement actions by priority and action type.
        """

        skill_gap_actions = sum(
            1
            for action in action_plan
            if action.get("type")
            in {
                "Skill Development",
                "Optional Skill Development",
                "Evidence Development",
                "Requirement Review",
            }
        )

        evidence_improvement_actions = sum(
            1
            for action in action_plan
            if action.get("type")
            == "Evidence Improvement"
        )

        return {
            "total_actions": len(
                action_plan
            ),
            "high_priority_actions": sum(
                1
                for action in action_plan
                if action.get("priority")
                == "High"
            ),
            "medium_priority_actions": sum(
                1
                for action in action_plan
                if action.get("priority")
                == "Medium"
            ),
            "low_priority_actions": sum(
                1
                for action in action_plan
                if action.get("priority")
                == "Low"
            ),
            "skill_gap_actions": skill_gap_actions,
            "evidence_improvement_actions": (
                evidence_improvement_actions
            ),
        }


if __name__ == "__main__":

    print(
        "ImprovementPlanner is ready."
    )