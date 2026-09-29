from __future__ import annotations

import re
from typing import Any

from models import create_empty_cv_profile


class CVAnalyzer:
    """
    Convert extracted CV text into a structured candidate profile.

    The analyzer is intentionally deterministic at this stage.
    Semantic matching will be handled later by the matching layer.
    """

    # =========================================================
    # SKILL CATEGORIES
    # =========================================================

    SKILL_CATEGORIES = {
        "programming": [
            "Python",
            "SQL",
            "C++",
            "C",
            "Java",
            "JavaScript",
            "TypeScript",
            "R",
        ],

        "data_analysis": [
            "Pandas",
            "NumPy",
            "Matplotlib",
            "Seaborn",
            "Power BI",
            "Microsoft Excel",
            "Excel",
        ],

        "machine_learning": [
            "Machine Learning",
            "Deep Learning",
            "Scikit-learn",
            "TensorFlow",
            "PyTorch",
            "Keras",
            "NLP",
            "Natural Language Processing",
        ],

        "databases": [
            "MySQL",
            "PostgreSQL",
            "MongoDB",
            "SQLite",
        ],

        "visualization": [
            "Power BI",
            "Matplotlib",
            "Seaborn",
            "Plotly",
            "Streamlit",
            "Tableau",
            "Data Visualization",
        ],

        "developer_tools": [
            "Git",
            "GitHub",
            "VS Code",
            "Docker",
            "Linux",
        ],

        "cloud": [
            "AWS",
            "Azure",
            "Google Cloud",
            "GCP",
        ],
    }

    # =========================================================
    # SECTION ALIASES
    # =========================================================

    SECTION_ALIASES = {

        "summary": {
            "summary",
            "professional summary",
            "profile",
            "professional profile",
            "career profile",
            "objective",
            "career objective",
            "about me",
        },

        "education": {
            "education",
            "educational background",
            "academic background",
            "academic qualifications",
            "academic profile",
            "education qualifications",
        },

        "skills": {
            "skills",
            "technical skills",
            "technical skill",
            "technical expertise",
            "skills & technologies",
            "skills and technologies",
            "technologies",
            "technical competencies",
            "core skills",
            "key skills",
        },

        "experience": {
            "experience",
            "work experience",
            "professional experience",
            "employment history",
            "work history",
            "internship",
            "internships",
            "internship experience",
            "professional experience",
        },

        "projects": {
            "projects",
            "project",
            "selected projects",
            "academic projects",
            "academic project",
            "personal projects",
            "key projects",
            "major projects",
        },

        "certifications": {
            "certifications",
            "certificates",
            "certification",
            "professional certifications",
            "courses & certifications",
            "courses and certifications",
        },

        "activities": {
            "activities",
            "achievements",
            "extracurricular activities",
            "extracurricular",
            "volunteering",
            "volunteer activities",
            "leadership & activities",
            "leadership and activities",
        },

        "languages": {
            "languages",
            "language",
            "spoken languages",
        },
    }

    COMBINED_SECTIONS = {
        "experience projects": (
            "experience_and_projects"
        ),
        "experience selected projects": (
            "experience_and_projects"
        ),
        "experience selected project": (
            "experience_and_projects"
        ),
        "work experience projects": (
            "experience_and_projects"
        ),
        "certifications activities": (
            "certifications_and_activities"
        ),
        "certifications achievements": (
            "certifications_and_activities"
        ),
        "certificates activities": (
            "certifications_and_activities"
        ),
    }

    # =========================================================
    # PUBLIC API
    # =========================================================

    def analyze(
        self,
        text: str,
        links: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Convert CV text and document links into a structured
        candidate profile.
        """

        if not text or not text.strip():

            raise ValueError(
                "CV text is empty."
            )

        profile = (
            create_empty_cv_profile()
        )

        cleaned_text = self._clean_text(
            text
        )

        profile["raw_text"] = (
            cleaned_text
        )

        sections = (
            self._extract_sections(
                cleaned_text
            )
        )

        profile["name"] = (
            self._extract_name(
                cleaned_text
            )
        )

        profile["contact"] = (
            self._extract_contact_information(
                cleaned_text,
                links or [],
            )
        )

        profile["summary"] = (
            sections
            .get("summary", "")
            .strip()
        )

        profile["education"] = (
            self._extract_entries(
                sections.get(
                    "education",
                    "",
                )
            )
        )

        # Search declared skills first and
        # supporting CV evidence second.
        evidence_text = "\n".join(
            [
                sections.get(
                    "experience",
                    "",
                ),
                sections.get(
                    "projects",
                    "",
                ),
                sections.get(
                    "certifications",
                    "",
                ),
            ]
        )

        profile["skills"] = (
            self._extract_skills(
                sections.get(
                    "skills",
                    "",
                ),
                evidence_text,
            )
        )

        profile["experience"] = (
            self._extract_entries(
                sections.get(
                    "experience",
                    "",
                )
            )
        )

        profile["projects"] = (
            self._extract_entries(
                sections.get(
                    "projects",
                    "",
                )
            )
        )

        profile["certifications"] = (
            self._extract_entries(
                sections.get(
                    "certifications",
                    "",
                )
            )
        )

        profile["activities"] = (
            self._extract_entries(
                sections.get(
                    "activities",
                    "",
                )
            )
        )

        profile["languages"] = (
            self._extract_languages(
                sections.get(
                    "languages",
                    "",
                )
            )
        )

        return profile

    # =========================================================
    # NAME
    # =========================================================

    def _extract_name(
        self,
        text: str,
    ) -> str:

        lines = [
            self._clean_line(line)
            for line in text.splitlines()
        ]

        lines = [
            line
            for line in lines
            if line
        ]

        for index, line in enumerate(lines[:10]):

            normalized = (
                self._normalize_heading(line)
            )

            if normalized in self._all_heading_names():
                continue

            if "@" in line:
                continue

            if self._looks_like_phone(line):
                continue

            if self._looks_like_url(line):
                continue

            # Contact lines often contain separators.
            if (
                "|" in line
                and (
                    "@" in line
                    or "linkedin" in line.lower()
                    or "github" in line.lower()
                )
            ):
                continue

            # Avoid selecting a very long paragraph.
            if len(line) > 100:
                continue

            # A name is usually short and near the top.
            if index < 5:
                return line

        return ""

    # =========================================================
    # CONTACT
    # =========================================================

    def _extract_contact_information(
        self,
        text: str,
        links: list[str],
    ) -> dict[str, str]:

        contact = {
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
        }

        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\."
            r"[A-Za-z]{2,}\b",
            text,
        )

        if email_match:
            contact["email"] = (
                email_match.group(0)
            )

        contact["phone"] = (
            self._extract_phone(text)
        )

        # Embedded document links.
        for link in links:

            normalized = link.lower()

            if (
                "linkedin.com" in normalized
                and not contact["linkedin"]
            ):
                contact["linkedin"] = (
                    link
                )

            elif (
                "github.com" in normalized
                and not contact["github"]
            ):
                contact["github"] = (
                    link
                )

        # URL fallback.
        if not contact["linkedin"]:

            linkedin_match = re.search(
                r"(?:https?://)?"
                r"(?:www\.)?"
                r"linkedin\.com/[^\s|]+",
                text,
                flags=re.IGNORECASE,
            )

            if linkedin_match:
                contact["linkedin"] = (
                    linkedin_match.group(0)
                )

        if not contact["github"]:

            github_match = re.search(
                r"(?:https?://)?"
                r"(?:www\.)?"
                r"github\.com/[^\s|]+",
                text,
                flags=re.IGNORECASE,
            )

            if github_match:
                contact["github"] = (
                    github_match.group(0)
                )

        return contact

    @classmethod
    def _extract_phone(
        cls,
        text: str,
    ) -> str:

        # First inspect contact-related lines.
        lines = text.splitlines()

        candidates: list[str] = []

        for line in lines:

            lower = line.lower()

            if any(
                keyword in lower
                for keyword in (
                    "phone",
                    "mobile",
                    "telephone",
                    "tel",
                    "contact",
                )
            ):
                candidates.append(line)

        # Then fall back to the first plausible
        # international/national phone number.
        candidates.extend(lines)

        pattern = re.compile(
            r"(?<!\d)"
            r"(?:\+\d{1,3}[\s.-]?)?"
            r"(?:\(?\d{2,4}\)?[\s.-]?)?"
            r"\d[\d\s.-]{6,}\d"
            r"(?!\d)"
        )

        for line in candidates:

            for match in pattern.finditer(line):

                candidate = (
                    match.group(0)
                    .strip()
                )

                digits = re.sub(
                    r"\D",
                    "",
                    candidate,
                )

                # Real phone numbers normally contain
                # 8-15 digits.
                if 8 <= len(digits) <= 15:

                    # Reject obvious academic years.
                    if (
                        len(digits) == 4
                        and 1900 <= int(digits) <= 2100
                    ):
                        continue

                    return candidate

        return ""

    @staticmethod
    def _looks_like_phone(
        text: str,
    ) -> bool:

        digits = re.sub(
            r"\D",
            "",
            text,
        )

        return 8 <= len(digits) <= 15

    @staticmethod
    def _looks_like_url(
        text: str,
    ) -> bool:

        lower = text.lower()

        return (
            "http://" in lower
            or "https://" in lower
            or "linkedin.com" in lower
            or "github.com" in lower
        )

    # =========================================================
    # SECTION EXTRACTION
    # =========================================================

    def _extract_sections(
        self,
        text: str,
    ) -> dict[str, str]:

        lines = [
            self._clean_line(line)
            for line in text.splitlines()
        ]

        lines = [
            line
            for line in lines
            if line
        ]

        heading_lookup: dict[
            str,
            str,
        ] = {}

        for canonical, aliases in (
            self.SECTION_ALIASES.items()
        ):

            for alias in aliases:

                heading_lookup[
                    self._normalize_heading(alias)
                ] = canonical

        sections: dict[
            str,
            list[str],
        ] = {}

        combined_sections: dict[
            str,
            list[str],
        ] = {
            "experience_and_projects": [],
            "certifications_and_activities": [],
        }

        current_section: (
            str | None
        ) = None

        for line in lines:

            normalized = (
                self._normalize_heading(
                    line
                )
            )

            # ---------------------------------------------
            # Combined section
            # ---------------------------------------------

            if normalized in self.COMBINED_SECTIONS:

                current_section = (
                    self.COMBINED_SECTIONS[
                        normalized
                    ]
                )

                continue

            # ---------------------------------------------
            # Normal section
            # ---------------------------------------------

            if normalized in heading_lookup:

                current_section = (
                    heading_lookup[
                        normalized
                    ]
                )

                sections.setdefault(
                    current_section,
                    [],
                )

                continue

            # ---------------------------------------------
            # Ignore content before the first heading
            # only if it looks like a document title/contact.
            # The name/contact are separately extracted.
            # ---------------------------------------------

            if current_section is None:
                continue

            if current_section in combined_sections:

                combined_sections[
                    current_section
                ].append(line)

            else:

                sections.setdefault(
                    current_section,
                    [],
                )

                sections[
                    current_section
                ].append(line)

        self._split_experience_projects(
            sections,
            combined_sections[
                "experience_and_projects"
            ],
        )

        self._split_certifications_activities(
            sections,
            combined_sections[
                "certifications_and_activities"
            ],
        )

        return {
            section: "\n".join(
                values
            )
            for section, values in sections.items()
            if values
        }

    # =========================================================
    # COMBINED EXPERIENCE / PROJECTS
    # =========================================================

    def _split_experience_projects(
        self,
        sections: dict[str, list[str]],
        lines: list[str],
    ) -> None:

        if not lines:
            return

        experience_lines: list[str] = []
        project_lines: list[str] = []

        project_started = False

        for line in lines:

            normalized = line.lower().strip()

            if self._is_project_start(
                normalized
            ):
                project_started = True

            if project_started:
                project_lines.append(line)
            else:
                experience_lines.append(line)

        if experience_lines:

            sections["experience"] = (
                experience_lines
            )

        if project_lines:

            sections["projects"] = (
                project_lines
            )

    @staticmethod
    def _is_project_start(
        normalized_line: str,
    ) -> bool:

        patterns = (
            r"^project\s*:",
            r"^projects\s*:",
            r"^selected project\s*:",
            r"^selected projects\s*:",
            r"^project\s+-",
            r"^project\s+\|",
        )

        return any(
            re.search(
                pattern,
                normalized_line,
            )
            for pattern in patterns
        )

    # =========================================================
    # COMBINED CERTIFICATIONS / ACTIVITIES
    # =========================================================

    def _split_certifications_activities(
        self,
        sections: dict[str, list[str]],
        lines: list[str],
    ) -> None:

        if not lines:
            return

        certification_lines: list[str] = []
        activity_lines: list[str] = []

        for line in lines:

            normalized = (
                line.lower().strip()
            )

            if self._looks_like_activity(
                normalized
            ):
                activity_lines.append(
                    line
                )
            else:
                certification_lines.append(
                    line
                )

        if certification_lines:

            sections["certifications"] = (
                certification_lines
            )

        if activity_lines:

            sections["activities"] = (
                activity_lines
            )

    @staticmethod
    def _looks_like_activity(
        normalized_line: str,
    ) -> bool:

        prefixes = (
            "participated",
            "member",
            "volunteered",
            "volunteering",
            "organized",
            "coordinated",
            "served as",
            "led",
        )

        if normalized_line.startswith(
            prefixes
        ):
            return True

        activity_phrases = (
            "volunteering activities",
            "extracurricular activities",
            "club member",
            "student member",
        )

        return any(
            phrase in normalized_line
            for phrase in activity_phrases
        )

    # =========================================================
    # LANGUAGES
    # =========================================================

    @staticmethod
    def _extract_languages(
        section_text: str,
    ) -> list[str]:

        if not section_text.strip():
            return []

        entries: list[str] = []

        for line in section_text.splitlines():

            cleaned = (
                " ".join(
                    line.split()
                ).strip()
            )

            if cleaned:
                entries.append(
                    cleaned
                )

        return entries

    # =========================================================
    # SKILLS
    # =========================================================

    def _extract_skills(
        self,
        skills_section: str,
        evidence_text: str,
    ) -> dict[str, list[str]]:

        result = {
            category: []
            for category in self.SKILL_CATEGORIES
        }

        # Skills explicitly declared in the Skills section
        # receive priority.
        declared_text = (
            skills_section or ""
        )

        # Supporting evidence can demonstrate skills
        # even if the candidate did not repeat them in
        # the Skills section.
        supporting_text = (
            evidence_text or ""
        )

        for category, skills in (
            self.SKILL_CATEGORIES.items()
        ):

            for skill in skills:

                found_in_declared = (
                    self._contains_skill(
                        declared_text,
                        skill,
                    )
                )

                found_in_evidence = (
                    self._contains_skill(
                        supporting_text,
                        skill,
                    )
                )

                if (
                    found_in_declared
                    or found_in_evidence
                ):

                    canonical = (
                        self._canonicalize_skill(
                            skill
                        )
                    )

                    if canonical not in result[
                        category
                    ]:

                        result[
                            category
                        ].append(
                            canonical
                        )

        return result

    @staticmethod
    def _canonicalize_skill(
        skill: str,
    ) -> str:

        aliases = {
            "Numpy": "NumPy",
            "numpy": "NumPy",
            "Sql": "SQL",
            "sql": "SQL",
            "Excel": "Microsoft Excel",
            "Powerbi": "Power BI",
            "Scikit Learn": "Scikit-learn",
        }

        return aliases.get(
            skill,
            skill,
        )

    @staticmethod
    def _contains_skill(
        text: str,
        skill: str,
    ) -> bool:

        if not text:
            return False

        escaped_skill = (
            re.escape(skill)
        )

        pattern = (
            rf"(?<![A-Za-z0-9+#.-])"
            rf"{escaped_skill}"
            rf"(?![A-Za-z0-9+#.-])"
        )

        return bool(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    # =========================================================
    # GENERIC ENTRIES
    # =========================================================

    @staticmethod
    def _extract_entries(
        section_text: str,
    ) -> list[str]:

        if not section_text.strip():
            return []

        entries: list[str] = []

        for line in section_text.splitlines():

            cleaned = (
                " ".join(
                    line.split()
                ).strip()
            )

            if cleaned:
                entries.append(
                    cleaned
                )

        return entries

    # =========================================================
    # HEADING UTILITIES
    # =========================================================

    @classmethod
    def _all_heading_names(
        cls,
    ) -> set[str]:

        result: set[str] = set()

        for aliases in (
            cls.SECTION_ALIASES.values()
        ):

            for alias in aliases:

                result.add(
                    cls._normalize_heading(
                        alias
                    )
                )

        result.update(
            cls.COMBINED_SECTIONS.keys()
        )

        return result

    @staticmethod
    def _normalize_heading(
        value: str,
    ) -> str:

        value = (
            value.lower()
            .strip()
        )

        # Remove common heading numbering.
        value = re.sub(
            r"^\s*\d+(?:\.\d+)*[\s.)-]+",
            "",
            value,
        )

        # Remove trailing colon.
        value = re.sub(
            r":+$",
            "",
            value,
        )

        value = re.sub(
            r"[&|:/_-]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _clean_line(
        line: str,
    ) -> str:

        return (
            " ".join(
                line.split()
            ).strip()
        )

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:

        return "\n".join(
            [
                " ".join(
                    line.split()
                ).strip()
                for line in text.splitlines()
                if " ".join(
                    line.split()
                ).strip()
            ]
        )


if __name__ == "__main__":

    print(
        "CVAnalyzer is ready."
    )