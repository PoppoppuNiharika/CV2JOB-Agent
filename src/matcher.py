from __future__ import annotations

from typing import Any, Iterable


class CVJobMatcher:
    """
    Deterministic CV-to-job matching engine.

    Responsibilities:
    - Match CV technical skills against required job skills.
    - Match CV technical skills against preferred job skills.
    - Match CV soft skills against job soft skills.
    - Normalize equivalent skill names.
    - Calculate transparent match percentages.
    - Report matched, missing, and extra CV skills.

    This class intentionally performs deterministic matching only.

    Semantic similarity and evidence strength are handled later by:
        - EvidenceMapper
        - SemanticMatcher
        - IntegratedMatcher
    """

    # --------------------------------------------------------------
    # Default scoring weights
    # --------------------------------------------------------------

    REQUIRED_WEIGHT = 0.70
    PREFERRED_WEIGHT = 0.20
    SOFT_SKILL_WEIGHT = 0.10

    # --------------------------------------------------------------
    # Main public method
    # --------------------------------------------------------------

    def match(
        self,
        cv_profile: dict[str, Any],
        job_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compare a structured CV profile against a structured
        job profile.

        Parameters
        ----------
        cv_profile:
            Structured CV profile produced by CVAnalyzer.

        job_profile:
            Structured job profile produced by JobAnalyzer.

        Returns
        -------
        dict
            Structured deterministic matching result.
        """

        self._validate_profile(
            cv_profile,
            "CV profile",
        )

        self._validate_profile(
            job_profile,
            "Job profile",
        )

        cv_skills = self._collect_cv_skills(
            cv_profile
        )

        required_skills = self._clean_skill_list(
            job_profile.get(
                "required_skills",
                [],
            )
        )

        preferred_skills = self._clean_skill_list(
            job_profile.get(
                "preferred_skills",
                [],
            )
        )

        job_soft_skills = self._clean_skill_list(
            job_profile.get(
                "soft_skills",
                [],
            )
        )

        cv_soft_skills = self._collect_cv_soft_skills(
            cv_profile
        )

        required_result = self._match_skill_group(
            cv_skills,
            required_skills,
        )

        preferred_result = self._match_skill_group(
            cv_skills,
            preferred_skills,
        )

        soft_skill_result = self._match_skill_group(
            cv_soft_skills,
            job_soft_skills,
        )

        overall_percentage = (
            self._calculate_overall_match(
                required_result,
                preferred_result,
                soft_skill_result,
            )
        )

        return {
            "job_title": job_profile.get(
                "job_title",
                "",
            ),

            "required_skills": required_result,

            "preferred_skills": preferred_result,

            "soft_skills": soft_skill_result,

            "cv_skills": cv_skills,

            "cv_soft_skills": cv_soft_skills,

            "overall_match_percentage": (
                overall_percentage
            ),
        }

    # ==============================================================
    # VALIDATION
    # ==============================================================

    @staticmethod
    def _validate_profile(
        profile: Any,
        profile_name: str,
    ) -> None:
        """
        Validate the minimum structure expected by the matcher.
        """

        if profile is None:
            raise ValueError(
                f"{profile_name} is empty."
            )

        if not isinstance(profile, dict):
            raise TypeError(
                f"{profile_name} must be a dictionary."
            )

        if not profile:
            raise ValueError(
                f"{profile_name} is empty."
            )

    # ==============================================================
    # COLLECT CV TECHNICAL SKILLS
    # ==============================================================

    @classmethod
    def _collect_cv_skills(
        cls,
        cv_profile: dict[str, Any],
    ) -> list[str]:
        """
        Collect technical skills from every CV skill category.

        The CVAnalyzer stores skills under:

            programming
            data_analysis
            machine_learning
            databases
            visualization
            developer_tools
            cloud
            other
        """

        skills_section = cv_profile.get(
            "skills",
            {},
        )

        if not isinstance(
            skills_section,
            dict,
        ):
            return []

        collected: list[str] = []

        for category_skills in (
            skills_section.values()
        ):

            if not isinstance(
                category_skills,
                list,
            ):
                continue

            for skill in category_skills:

                if not isinstance(
                    skill,
                    str,
                ):
                    continue

                normalized = cls._normalize_skill(
                    skill
                )

                if (
                    normalized
                    and normalized not in collected
                ):
                    collected.append(
                        normalized
                    )

        return collected

    # ==============================================================
    # COLLECT CV SOFT SKILLS
    # ==============================================================

    @classmethod
    def _collect_cv_soft_skills(
        cls,
        cv_profile: dict[str, Any],
    ) -> list[str]:
        """
        Collect soft skills from explicit CV strengths and
        textual CV evidence.

        Soft-skill detection here is intentionally conservative.
        The matcher should not claim a soft skill merely because
        an unrelated word happens to occur in the CV.
        """

        collected: list[str] = []

        skills_section = cv_profile.get(
            "skills",
            {},
        )

        if isinstance(
            skills_section,
            dict,
        ):
            core_strengths = skills_section.get(
                "other",
                [],
            )

            if isinstance(
                core_strengths,
                list,
            ):
                for skill in core_strengths:

                    if not isinstance(
                        skill,
                        str,
                    ):
                        continue

                    normalized = cls._normalize_soft_skill(
                        skill
                    )

                    if (
                        normalized
                        and normalized not in collected
                    ):
                        collected.append(
                            normalized
                        )

        raw_text = cv_profile.get(
            "raw_text",
            "",
        )

        if isinstance(
            raw_text,
            str,
        ):
            detected = cls._extract_soft_skills_from_text(
                raw_text
            )

            for skill in detected:

                if skill not in collected:
                    collected.append(
                        skill
                    )

        return collected

    # ==============================================================
    # SOFT-SKILL TEXT EXTRACTION
    # ==============================================================

    @classmethod
    def _extract_soft_skills_from_text(
        cls,
        text: str,
    ) -> list[str]:
        """
        Detect common soft-skill expressions in CV text.
        """

        normalized_text = (
            " ".join(
                text.lower().split()
            )
        )

        aliases = {
            "Analytical Thinking": [
                "analytical thinking",
                "analytical skills",
                "strong analytical",
            ],

            "Problem Solving": [
                "problem solving",
                "problem-solving",
                "problem solving skills",
                "problem-solving skills",
            ],

            "Communication": [
                "communication",
                "communication skills",
                "communicate",
                "communicating",
            ],

            "Teamwork": [
                "teamwork",
                "team work",
                "team player",
            ],

            "Collaboration": [
                "collaboration",
                "collaborate",
                "collaborative",
                "collaborating",
            ],

            "Leadership": [
                "leadership",
                "leadership skills",
            ],

            "Critical Thinking": [
                "critical thinking",
                "critical-thinking",
            ],

            "Time Management": [
                "time management",
            ],

            "Adaptability": [
                "adaptability",
                "adaptable",
            ],

            "Attention to Detail": [
                "attention to detail",
                "detail-oriented",
                "detail oriented",
            ],
        }

        found: list[str] = []

        for canonical_name, skill_aliases in (
            aliases.items()
        ):

            for alias in skill_aliases:

                if alias in normalized_text:

                    found.append(
                        canonical_name
                    )

                    break

        return found

    # ==============================================================
    # MATCH A REQUIREMENT GROUP
    # ==============================================================

    @classmethod
    def _match_skill_group(
        cls,
        cv_skills: Iterable[str],
        job_skills: Iterable[str],
    ) -> dict[str, Any]:
        """
        Match one requirement group against CV skills.

        Returns:
            matched
            missing
            total_required
            match_percentage
        """

        cleaned_cv_skills = cls._clean_skill_list(
            cv_skills
        )

        cleaned_job_skills = cls._clean_skill_list(
            job_skills
        )

        normalized_cv_skills = {
            cls._normalize_skill(skill)
            for skill in cleaned_cv_skills
        }

        normalized_cv_skills.discard("")

        matched: list[str] = []
        missing: list[str] = []

        for job_skill in cleaned_job_skills:

            normalized_job_skill = (
                cls._normalize_skill(
                    job_skill
                )
            )

            if (
                normalized_job_skill
                in normalized_cv_skills
            ):
                matched.append(
                    job_skill
                )
            else:
                missing.append(
                    job_skill
                )

        total = len(
            cleaned_job_skills
        )

        percentage = cls._calculate_percentage(
            len(matched),
            total,
        )

        return {
            "matched": matched,
            "missing": missing,
            "total_required": total,
            "match_percentage": percentage,
        }

    # ==============================================================
    # PERCENTAGE
    # ==============================================================

    @staticmethod
    def _calculate_percentage(
        matched_count: int,
        total_count: int,
    ) -> float:
        """
        Calculate a percentage safely.
        """

        if total_count <= 0:
            return 0.0

        percentage = (
            matched_count
            / total_count
        ) * 100

        return round(
            percentage,
            2,
        )

    # ==============================================================
    # OVERALL MATCH
    # ==============================================================

    @classmethod
    def _calculate_overall_match(
        cls,
        required_result: dict[str, Any],
        preferred_result: dict[str, Any],
        soft_skill_result: dict[str, Any],
    ) -> float:
        """
        Calculate the deterministic overall match.

        Default weighting:

            Required skills   = 70%
            Preferred skills  = 20%
            Soft skills       = 10%

        Categories with zero requirements are excluded from the
        denominator so a JD does not penalize a candidate for
        requirements that do not exist.

        This is a deterministic compatibility score, not a claim
        about hiring probability or candidate quality.
        """

        weighted_scores: list[float] = []
        weights: list[float] = []

        category_data = [
            (
                required_result,
                cls.REQUIRED_WEIGHT,
            ),
            (
                preferred_result,
                cls.PREFERRED_WEIGHT,
            ),
            (
                soft_skill_result,
                cls.SOFT_SKILL_WEIGHT,
            ),
        ]

        for result, weight in category_data:

            total = result.get(
                "total_required",
                0,
            )

            if total <= 0:
                continue

            score = float(
                result.get(
                    "match_percentage",
                    0.0,
                )
            )

            weighted_scores.append(
                score
            )

            weights.append(
                weight
            )

        if not weighted_scores:
            return 0.0

        total_weight = sum(
            weights
        )

        if total_weight <= 0:
            return 0.0

        weighted_average = (
            sum(
                score * weight
                for score, weight in zip(
                    weighted_scores,
                    weights,
                )
            )
            / total_weight
        )

        return round(
            weighted_average,
            2,
        )

    # ==============================================================
    # CLEAN SKILL LIST
    # ==============================================================

    @classmethod
    def _clean_skill_list(
        cls,
        skills: Iterable[str] | None,
    ) -> list[str]:
        """
        Clean and deduplicate a skill list while preserving order.
        """

        if skills is None:
            return []

        if isinstance(
            skills,
            str,
        ):
            skills = [skills]

        cleaned: list[str] = []
        seen: set[str] = set()

        for skill in skills:

            if not isinstance(
                skill,
                str,
            ):
                continue

            skill = skill.strip()

            if not skill:
                continue

            normalized = cls._normalize_skill(
                skill
            )

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            cleaned.append(
                skill
            )

        return cleaned

    # ==============================================================
    # SKILL NORMALIZATION
    # ==============================================================

    @staticmethod
    def _normalize_skill(
        skill: str,
    ) -> str:
        """
        Normalize technical skill names.

        The normalized value is used internally for comparison.
        Original job skill spelling is preserved in output.
        """

        if not isinstance(
            skill,
            str,
        ):
            return ""

        normalized = (
            skill
            .strip()
            .lower()
        )

        normalized = (
            normalized
            .replace("–", "-")
            .replace("—", "-")
        )

        normalized = " ".join(
            normalized.split()
        )

        aliases = {
            "numpy": "numpy",
            "num py": "numpy",

            "sql": "sql",

            "python": "python",

            "c++": "c++",

            "excel": "microsoft excel",
            "microsoft excel": "microsoft excel",

            "powerbi": "power bi",
            "power bi": "power bi",

            "scikit learn": "scikit-learn",
            "scikit-learn": "scikit-learn",
            "sklearn": "scikit-learn",

            "git": "git",
            "github": "github",

            "git & github": "git github",

            "data analysis": "data analysis",

            "data visualization": (
                "data visualization"
            ),

            "data visualisation": (
                "data visualization"
            ),

            "machine learning": (
                "machine learning"
            ),

            "deep learning": (
                "deep learning"
            ),

            "artificial intelligence": (
                "artificial intelligence"
            ),

            "ai": "artificial intelligence",

            "problem-solving": (
                "problem solving"
            ),

            "problem solving": (
                "problem solving"
            ),

            "analytical": (
                "analytical thinking"
            ),

            "analytical skills": (
                "analytical thinking"
            ),

            "analytical thinking": (
                "analytical thinking"
            ),
        }

        return aliases.get(
            normalized,
            normalized,
        )

    # ==============================================================
    # SOFT-SKILL NORMALIZATION
    # ==============================================================

    @classmethod
    def _normalize_soft_skill(
        cls,
        skill: str,
    ) -> str:
        """
        Normalize a soft skill to the same vocabulary used by
        the JobAnalyzer.
        """

        if not isinstance(
            skill,
            str,
        ):
            return ""

        normalized = (
            " ".join(
                skill.lower().split()
            )
        )

        aliases = {
            "analytical": (
                "Analytical Thinking"
            ),

            "analytical skills": (
                "Analytical Thinking"
            ),

            "analytical thinking": (
                "Analytical Thinking"
            ),

            "strong analytical": (
                "Analytical Thinking"
            ),

            "problem solving": (
                "Problem Solving"
            ),

            "problem-solving": (
                "Problem Solving"
            ),

            "communication": (
                "Communication"
            ),

            "communication skills": (
                "Communication"
            ),

            "teamwork": (
                "Teamwork"
            ),

            "team work": (
                "Teamwork"
            ),

            "collaboration": (
                "Collaboration"
            ),

            "leadership": (
                "Leadership"
            ),

            "critical thinking": (
                "Critical Thinking"
            ),

            "time management": (
                "Time Management"
            ),

            "adaptability": (
                "Adaptability"
            ),

            "attention to detail": (
                "Attention to Detail"
            ),
        }

        return aliases.get(
            normalized,
            skill.strip(),
        )


if __name__ == "__main__":
    print(
        "CVJobMatcher is ready."
    )