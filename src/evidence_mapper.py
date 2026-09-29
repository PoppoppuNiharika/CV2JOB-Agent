from typing import Any
import re


class EvidenceMapper:
    """
    Map job requirements to supporting evidence in a CV.

    The mapper searches across:
    - Technical skills
    - Experience
    - Projects
    - Certifications
    - Activities
    - Soft skills
    - Raw CV text as a fallback

    This component is intentionally deterministic.

    Semantic similarity is handled later by SemanticMatcher.
    """

    # =========================================================
    # CONFIGURATION
    # =========================================================

    MAX_EVIDENCE_PER_REQUIREMENT = 5

    SOURCE_PRIORITY = {
        "Technical Skills": 1,
        "Core Strengths": 2,
        "Experience": 3,
        "Project": 4,
        "Certification": 5,
        "Activity": 6,
        "CV Text": 7,
    }

    # =========================================================
    # MAIN METHOD
    # =========================================================

    def map_evidence(
        self,
        cv_profile: dict[str, Any],
        job_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Map job requirements to supporting CV evidence.

        Args:
            cv_profile:
                Structured CV profile produced by CVAnalyzer.

            job_profile:
                Structured job profile produced by JobAnalyzer.

        Returns:
            Dictionary containing job title, requirement evidence,
            and summary statistics.
        """

        if not isinstance(cv_profile, dict):
            raise TypeError(
                "CV profile must be a dictionary."
            )

        if not cv_profile:
            raise ValueError(
                "CV profile is empty."
            )

        if not isinstance(job_profile, dict):
            raise TypeError(
                "Job profile must be a dictionary."
            )

        if not job_profile:
            raise ValueError(
                "Job profile is empty."
            )

        requirements = []

        # -----------------------------------------------------
        # Required skills
        # -----------------------------------------------------

        for skill in self._clean_requirement_list(
            job_profile.get(
                "required_skills",
                [],
            )
        ):

            evidence = self._find_evidence(
                skill,
                cv_profile,
            )

            requirements.append(
                self._create_result(
                    requirement=skill,
                    category="Required Skill",
                    evidence=evidence,
                )
            )

        # -----------------------------------------------------
        # Preferred skills
        # -----------------------------------------------------

        for skill in self._clean_requirement_list(
            job_profile.get(
                "preferred_skills",
                [],
            )
        ):

            evidence = self._find_evidence(
                skill,
                cv_profile,
            )

            requirements.append(
                self._create_result(
                    requirement=skill,
                    category="Preferred Skill",
                    evidence=evidence,
                )
            )

        # -----------------------------------------------------
        # Soft skills
        # -----------------------------------------------------

        for skill in self._clean_requirement_list(
            job_profile.get(
                "soft_skills",
                [],
            )
        ):

            evidence = self._find_evidence(
                skill,
                cv_profile,
            )

            requirements.append(
                self._create_result(
                    requirement=skill,
                    category="Soft Skill",
                    evidence=evidence,
                )
            )

        return {
            "job_title": self._clean_text(
                job_profile.get(
                    "job_title",
                    "",
                )
            ),
            "requirements": requirements,
            "summary": self._create_summary(
                requirements
            ),
        }

    # =========================================================
    # FIND EVIDENCE
    # =========================================================

    def _find_evidence(
        self,
        requirement: str,
        cv_profile: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Search structured CV evidence first.

        Raw CV text is used only when no structured evidence
        has been found.
        """

        evidence = []

        normalized_requirement = self._normalize(
            requirement
        )

        if not normalized_requirement:
            return []

        # -----------------------------------------------------
        # 1. Technical skills / core strengths
        # -----------------------------------------------------

        skills_section = cv_profile.get(
            "skills",
            {},
        )

        if isinstance(
            skills_section,
            dict,
        ):

            for category, skills in skills_section.items():

                if not isinstance(
                    skills,
                    list,
                ):
                    continue

                source = self._skill_source(
                    category
                )

                for skill in skills:

                    if not isinstance(
                        skill,
                        str,
                    ):
                        continue

                    if self._skills_match(
                        requirement,
                        skill,
                    ):

                        evidence.append(
                            {
                                "source": source,
                                "category": self._clean_text(
                                    category
                                ),
                                "text": self._clean_text(
                                    skill
                                ),
                            }
                        )

        # -----------------------------------------------------
        # 2. Explicit soft skills
        # -----------------------------------------------------

        soft_skills = cv_profile.get(
            "soft_skills",
            [],
        )

        if isinstance(
            soft_skills,
            list,
        ):

            for skill in soft_skills:

                if not isinstance(
                    skill,
                    str,
                ):
                    continue

                if self._skills_match(
                    requirement,
                    skill,
                ):

                    evidence.append(
                        {
                            "source": "Core Strengths",
                            "category": "Soft Skills",
                            "text": self._clean_text(
                                skill
                            ),
                        }
                    )

        # -----------------------------------------------------
        # 3. Experience
        # -----------------------------------------------------

        for experience in self._as_list(
            cv_profile.get(
                "experience",
                [],
            )
        ):

            self._search_structured_item(
                requirement=normalized_requirement,
                item=experience,
                source="Experience",
                evidence=evidence,
            )

        # -----------------------------------------------------
        # 4. Projects
        # -----------------------------------------------------

        for project in self._as_list(
            cv_profile.get(
                "projects",
                [],
            )
        ):

            self._search_structured_item(
                requirement=normalized_requirement,
                item=project,
                source="Project",
                evidence=evidence,
            )

        # -----------------------------------------------------
        # 5. Certifications
        # -----------------------------------------------------

        for certification in self._as_list(
            cv_profile.get(
                "certifications",
                [],
            )
        ):

            self._search_structured_item(
                requirement=normalized_requirement,
                item=certification,
                source="Certification",
                evidence=evidence,
            )

        # -----------------------------------------------------
        # 6. Activities
        # -----------------------------------------------------

        for activity in self._as_list(
            cv_profile.get(
                "activities",
                [],
            )
        ):

            self._search_structured_item(
                requirement=normalized_requirement,
                item=activity,
                source="Activity",
                evidence=evidence,
            )

        # -----------------------------------------------------
        # 7. Raw CV text fallback
        # -----------------------------------------------------

        # Important:
        # Raw text is added only when structured evidence
        # was not found. This prevents giant duplicate
        # CV snippets from appearing for explicit skills.
        if not evidence:

            raw_text = cv_profile.get(
                "raw_text",
                "",
            )

            if isinstance(
                raw_text,
                str,
            ) and raw_text.strip():

                snippet = self._extract_text_snippet(
                    requirement=requirement,
                    text=raw_text,
                )

                if snippet:

                    evidence.append(
                        {
                            "source": "CV Text",
                            "category": "Raw CV",
                            "text": snippet,
                        }
                    )

        # -----------------------------------------------------
        # 8. Clean and rank evidence
        # -----------------------------------------------------

        evidence = self._remove_duplicate_evidence(
            evidence
        )

        evidence.sort(
            key=self._evidence_sort_key
        )

        return evidence[
            : self.MAX_EVIDENCE_PER_REQUIREMENT
        ]

    # =========================================================
    # SEARCH STRUCTURED ITEM
    # =========================================================

    def _search_structured_item(
        self,
        requirement: str,
        item: Any,
        source: str,
        evidence: list[dict[str, str]],
    ) -> None:
        """
        Search a structured CV item.

        Supports:
        - strings
        - dictionaries
        - lists inside dictionaries
        """

        if isinstance(
            item,
            str,
        ):

            cleaned_item = self._clean_text(
                item
            )

            if self._text_contains_requirement(
                requirement,
                cleaned_item,
            ):

                evidence.append(
                    {
                        "source": source,
                        "category": source,
                        "text": cleaned_item,
                    }
                )

            return

        if isinstance(
            item,
            list,
        ):

            for list_item in item:

                self._search_structured_item(
                    requirement=requirement,
                    item=list_item,
                    source=source,
                    evidence=evidence,
                )

            return

        if not isinstance(
            item,
            dict,
        ):
            return

        for key, value in item.items():

            # -------------------------------------------------
            # String value
            # -------------------------------------------------

            if isinstance(
                value,
                str,
            ):

                cleaned_value = self._clean_text(
                    value
                )

                if self._text_contains_requirement(
                    requirement,
                    cleaned_value,
                ):

                    evidence.append(
                        {
                            "source": source,
                            "category": self._clean_text(
                                key
                            ),
                            "text": cleaned_value,
                        }
                    )

            # -------------------------------------------------
            # List value
            # -------------------------------------------------

            elif isinstance(
                value,
                list,
            ):

                for list_item in value:

                    if not isinstance(
                        list_item,
                        str,
                    ):
                        continue

                    cleaned_item = self._clean_text(
                        list_item
                    )

                    if self._text_contains_requirement(
                        requirement,
                        cleaned_item,
                    ):

                        evidence.append(
                            {
                                "source": source,
                                "category": self._clean_text(
                                    key
                                ),
                                "text": cleaned_item,
                            }
                        )

    # =========================================================
    # CREATE RESULT
    # =========================================================

    @staticmethod
    def _create_result(
        requirement: str,
        category: str,
        evidence: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Create standardized requirement output.
        """

        status = (
            "Evidence Found"
            if evidence
            else "Gap"
        )

        return {
            "requirement": requirement,
            "category": category,
            "status": status,
            "evidence": evidence,
        }

    # =========================================================
    # SUMMARY
    # =========================================================

    @staticmethod
    def _create_summary(
        requirements: list[dict[str, Any]],
    ) -> dict[str, int]:
        """
        Create evidence coverage statistics.
        """

        evidence_found = sum(
            1
            for item in requirements
            if item.get(
                "status"
            ) == "Evidence Found"
        )

        gaps = sum(
            1
            for item in requirements
            if item.get(
                "status"
            ) == "Gap"
        )

        return {
            "total_requirements": len(
                requirements
            ),
            "evidence_found": evidence_found,
            "gaps": gaps,
        }

    # =========================================================
    # SKILL MATCHING
    # =========================================================

    @classmethod
    def _skills_match(
        cls,
        requirement: str,
        cv_skill: str,
    ) -> bool:
        """
        Compare two explicit skill names.

        Uses canonical aliases for common naming differences.
        """

        requirement_normalized = cls._normalize(
            requirement
        )

        skill_normalized = cls._normalize(
            cv_skill
        )

        if not requirement_normalized:
            return False

        if not skill_normalized:
            return False

        if requirement_normalized == skill_normalized:
            return True

        aliases = {
            "numpy": {
                "numpy",
                "num py",
            },

            "microsoft excel": {
                "microsoft excel",
                "excel",
            },

            "power bi": {
                "power bi",
                "powerbi",
            },

            "scikit learn": {
                "scikit learn",
                "scikit-learn",
                "sklearn",
            },

            "problem solving": {
                "problem solving",
                "problem-solving",
            },

            "analytical thinking": {
                "analytical thinking",
                "analytical skills",
                "analytical",
            },

            "data analysis": {
                "data analysis",
                "data analytics",
            },

            "data visualization": {
                "data visualization",
                "data visualisation",
            },

            "machine learning": {
                "machine learning",
                "machine-learning",
                "ml",
            },

            "github": {
                "github",
                "git hub",
            },
        }

        canonical_requirement = cls._canonical_alias(
            requirement_normalized,
            aliases,
        )

        canonical_skill = cls._canonical_alias(
            skill_normalized,
            aliases,
        )

        return (
            canonical_requirement
            == canonical_skill
        )

    # =========================================================
    # TEXT MATCHING
    # =========================================================

    @classmethod
    def _text_contains_requirement(
        cls,
        requirement: str,
        text: str,
    ) -> bool:
        """
        Determine whether a requirement is supported by text.

        The comparison is deterministic and uses aliases for
        common terminology.
        """

        requirement_normalized = cls._normalize(
            requirement
        )

        text_normalized = cls._normalize(
            text
        )

        if not requirement_normalized:
            return False

        if not text_normalized:
            return False

        aliases = {
            "data analysis": [
                "data analysis",
                "data analytics",
                "analyzed data",
                "analyze data",
                "analysed data",
                "analyse data",
            ],

            "data visualization": [
                "data visualization",
                "data visualisation",
                "visualization",
                "visualizations",
                "visualisation",
                "visualisations",
                "visualize data",
                "visualise data",
            ],

            "microsoft excel": [
                "microsoft excel",
                "excel",
            ],

            "power bi": [
                "power bi",
                "powerbi",
            ],

            "problem solving": [
                "problem solving",
                "problem-solving",
            ],

            "analytical thinking": [
                "analytical thinking",
                "analytical skills",
            ],

            "machine learning": [
                "machine learning",
                "machine-learning",
                "ml model",
                "ml models",
            ],

            "scikit learn": [
                "scikit learn",
                "scikit-learn",
                "sklearn",
            ],

            "github": [
                "github",
                "git hub",
            ],

            "git": [
                "git",
            ],
        }

        possible_phrases = aliases.get(
            requirement_normalized,
            [
                requirement_normalized
            ],
        )

        for phrase in possible_phrases:

            if cls._contains_phrase(
                text_normalized,
                phrase,
            ):
                return True

        return False

    # =========================================================
    # EXTRACT SNIPPET
    # =========================================================

    @classmethod
    def _extract_text_snippet(
        cls,
        requirement: str,
        text: str,
    ) -> str:
        """
        Extract a short relevant sentence or window from
        raw CV text.

        This prevents the mapper from returning the entire CV.
        """

        if not isinstance(
            text,
            str,
        ):
            return ""

        cleaned_text = cls._clean_text(
            text
        )

        if not cleaned_text:
            return ""

        # -----------------------------------------------------
        # Try sentence-level matching
        # -----------------------------------------------------

        sentences = re.split(
            r"(?<=[.!?])\s+",
            cleaned_text,
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            if cls._text_contains_requirement(
                requirement,
                sentence,
            ):

                return cls._limit_text(
                    sentence,
                    280,
                )

        # -----------------------------------------------------
        # Fallback: local text window
        # -----------------------------------------------------

        normalized_text = cls._normalize(
            cleaned_text
        )

        normalized_requirement = cls._normalize(
            requirement
        )

        possible_phrases = cls._possible_phrases(
            normalized_requirement
        )

        for phrase in possible_phrases:

            index = normalized_text.find(
                phrase
            )

            if index == -1:
                continue

            start = max(
                0,
                index - 100,
            )

            end = min(
                len(normalized_text),
                index + len(phrase) + 180,
            )

            snippet = normalized_text[
                start:end
            ].strip()

            return cls._limit_text(
                snippet,
                280,
            )

        return ""

    # =========================================================
    # DUPLICATE REMOVAL
    # =========================================================

    @classmethod
    def _remove_duplicate_evidence(
        cls,
        evidence: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """
        Remove duplicate evidence.

        Deduplication is based on source + normalized text,
        rather than source + category + text, so the same
        evidence is not displayed twice merely because it was
        discovered under two skill categories.
        """

        unique = []

        seen = set()

        for item in evidence:

            source = cls._normalize(
                item.get(
                    "source",
                    "",
                )
            )

            text = cls._normalize(
                item.get(
                    "text",
                    "",
                )
            )

            key = (
                source,
                text,
            )

            if not text:
                continue

            if key in seen:
                continue

            seen.add(key)

            unique.append(item)

        return unique

    # =========================================================
    # EVIDENCE SORTING
    # =========================================================

    @classmethod
    def _evidence_sort_key(
        cls,
        item: dict[str, str],
    ) -> tuple[int, int]:
        """
        Rank evidence so the strongest/direct sources appear
        first.
        """

        source = item.get(
            "source",
            "",
        )

        priority = cls.SOURCE_PRIORITY.get(
            source,
            99,
        )

        # Shorter explicit evidence is generally cleaner.
        text_length = len(
            item.get(
                "text",
                "",
            )
        )

        return (
            priority,
            text_length,
        )

    # =========================================================
    # SOURCE NORMALIZATION
    # =========================================================

    @staticmethod
    def _skill_source(
        category: Any,
    ) -> str:
        """
        Convert a CV skill category into a useful evidence source.
        """

        normalized = EvidenceMapper._normalize(
            category
        )

        if normalized in {
            "core strengths",
            "soft skills",
            "strengths",
        }:

            return "Core Strengths"

        return "Technical Skills"

    # =========================================================
    # CANONICAL ALIAS
    # =========================================================

    @staticmethod
    def _canonical_alias(
        value: str,
        aliases: dict[str, set[str]],
    ) -> str:
        """
        Return the canonical alias group for a value.
        """

        for canonical, variants in aliases.items():

            if value in variants:
                return canonical

        return value

    # =========================================================
    # POSSIBLE PHRASES
    # =========================================================

    @classmethod
    def _possible_phrases(
        cls,
        normalized_requirement: str,
    ) -> list[str]:
        """
        Return possible text representations of a requirement.
        """

        aliases = {
            "data analysis": [
                "data analysis",
                "data analytics",
                "analyzed data",
                "analyze data",
                "analysed data",
                "analyse data",
            ],

            "data visualization": [
                "data visualization",
                "data visualisation",
                "visualization",
                "visualizations",
                "visualisation",
                "visualisations",
                "visualize data",
                "visualise data",
            ],

            "microsoft excel": [
                "microsoft excel",
                "excel",
            ],

            "power bi": [
                "power bi",
                "powerbi",
            ],

            "problem solving": [
                "problem solving",
                "problem-solving",
            ],

            "analytical thinking": [
                "analytical thinking",
                "analytical skills",
                "analytical",
            ],

            "machine learning": [
                "machine learning",
                "machine-learning",
                "ml model",
                "ml models",
            ],

            "scikit learn": [
                "scikit learn",
                "scikit-learn",
                "sklearn",
            ],

            "github": [
                "github",
                "git hub",
            ],
        }

        return aliases.get(
            normalized_requirement,
            [
                normalized_requirement
            ],
        )

    # =========================================================
    # TEXT HELPERS
    # =========================================================

    @staticmethod
    def _contains_phrase(
        text: str,
        phrase: str,
    ) -> bool:
        """
        Check for a phrase using normalized text.
        """

        if not text or not phrase:
            return False

        return phrase in text

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        """
        Normalize whitespace while preserving useful content.
        """

        if not isinstance(
            value,
            str,
        ):
            return ""

        value = value.replace(
            "\u00a0",
            " ",
        )

        value = value.replace(
            "\r",
            " ",
        )

        value = value.replace(
            "\n",
            " ",
        )

        return " ".join(
            value.split()
        ).strip()

    @staticmethod
    def _normalize(
        value: Any,
    ) -> str:
        """
        Normalize text for deterministic comparison.
        """

        cleaned = EvidenceMapper._clean_text(
            value
        )

        return cleaned.lower()

    @staticmethod
    def _limit_text(
        text: str,
        maximum: int,
    ) -> str:
        """
        Limit long evidence while preserving complete words.
        """

        if len(text) <= maximum:
            return text

        shortened = text[
            :maximum
        ].rsplit(
            " ",
            1,
        )[0]

        return shortened.rstrip(
            " ,;:-"
        ) + "..."

    @staticmethod
    def _as_list(
        value: Any,
    ) -> list[Any]:
        """
        Safely convert a value to a list.
        """

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
            return value

        return [value]

    @staticmethod
    def _clean_requirement_list(
        value: Any,
    ) -> list[str]:
        """
        Clean and deduplicate requirement lists.
        """

        if not isinstance(
            value,
            list,
        ):
            return []

        result = []

        seen = set()

        for item in value:

            if not isinstance(
                item,
                str,
            ):
                continue

            cleaned = EvidenceMapper._clean_text(
                item
            )

            normalized = EvidenceMapper._normalize(
                cleaned
            )

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            result.append(
                cleaned
            )

        return result


if __name__ == "__main__":
    print(
        "EvidenceMapper is ready."
    )