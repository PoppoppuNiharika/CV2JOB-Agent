from typing import Dict, List, Optional
import re

from models import create_empty_job_profile


class JobAnalyzer:
    """
    Analyze a job description and extract structured information.

    Supports:
    - Explicitly sectioned job descriptions
    - Unusual section headings
    - Unstructured / paragraph-style job descriptions
    - Wrapped lines inside the same requirement paragraph
    """

    # ------------------------------------------------------------------
    # Skill vocabulary
    # ------------------------------------------------------------------

    SKILL_DICTIONARY = {
        "Python": [r"\bpython\b"],
        "SQL": [r"\bsql\b"],
        "C++": [r"\bc\+\+\b"],
        "C": [r"\bc\b"],
        "Java": [r"\bjava\b"],
        "JavaScript": [r"\bjavascript\b"],
        "TypeScript": [r"\btypescript\b"],
        "R": [r"\br\b"],

        "Pandas": [r"\bpandas\b"],
        "NumPy": [r"\bnumpy\b", r"\bnum\s*py\b"],

        "Data Analysis": [
            r"\bdata analysis\b",
            r"\banalytical analysis\b",
            r"\banalyzing data\b",
            r"\banalyse data\b",
            r"\banalyze data\b",
        ],

        "Data Visualization": [
            r"\bdata visualization\b",
            r"\bdata visualisation\b",
            r"\bvisualization of data\b",
            r"\bvisualisation of data\b",
            r"\bvisualize data\b",
            r"\bvisualise data\b",
        ],

        "Matplotlib": [r"\bmatplotlib\b"],
        "Seaborn": [r"\bseaborn\b"],

        "Microsoft Excel": [
            r"\bmicrosoft excel\b",
            r"\bexcel\b",
        ],

        "Power BI": [r"\bpower\s*bi\b"],
        "Tableau": [r"\btableau\b"],
        "Plotly": [r"\bplotly\b"],
        "Streamlit": [r"\bstreamlit\b"],

        "Scikit-learn": [
            r"\bscikit[- ]learn\b",
            r"\bsklearn\b",
        ],

        "Machine Learning": [
            r"\bmachine learning\b",
            r"\bml\b",
        ],

        "Deep Learning": [
            r"\bdeep learning\b",
        ],

        "Artificial Intelligence": [
            r"\bartificial intelligence\b",
            r"\bai\b",
        ],

        "NLP": [
            r"\bnatural language processing\b",
            r"\bnlp\b",
        ],

        "TensorFlow": [r"\btensorflow\b"],
        "PyTorch": [r"\bpytorch\b"],

        "Git": [r"\bgit\b"],
        "GitHub": [r"\bgithub\b"],
        "Docker": [r"\bdocker\b"],
        "Linux": [r"\blinux\b"],

        "AWS": [r"\baws\b"],
        "Azure": [r"\bazure\b"],

        "Google Cloud": [
            r"\bgoogle cloud\b",
            r"\bgcp\b",
        ],

        "REST API": [
            r"\brest api\b",
            r"\brestful api\b",
            r"\brestful services\b",
        ],

        "Flask": [r"\bflask\b"],
        "FastAPI": [r"\bfastapi\b"],
        "Django": [r"\bdjango\b"],

        "PostgreSQL": [r"\bpostgresql\b"],
        "MySQL": [r"\bmysql\b"],
        "MongoDB": [r"\bmongodb\b"],

        "Database": [
            r"\bdatabase\b",
            r"\bdatabases\b",
        ],
    }

    # ------------------------------------------------------------------
    # Section aliases
    # ------------------------------------------------------------------

    SECTION_ALIASES = {
        "required_skills": [
            "required skills",
            "required qualifications",
            "requirements",
            "minimum requirements",
            "minimum qualifications",
            "must have",
            "must-have",
            "mandatory skills",
            "mandatory qualifications",
            "technical requirements",
            "technical skills",
            "core requirements",
            "what you need",
            "what we are looking for",
            "what we're looking for",
        ],

        "preferred_skills": [
            "preferred skills",
            "preferred qualifications",
            "preferred requirements",
            "nice to have",
            "nice-to-have",
            "good to have",
            "desired skills",
            "desired qualifications",
            "bonus skills",
            "bonus qualifications",
            "additional skills",
        ],

        "responsibilities": [
            "responsibilities",
            "job responsibilities",
            "key responsibilities",
            "role responsibilities",
            "responsibility",
            "duties",
            "job duties",
            "what you will do",
            "what you'll do",
            "what you do",
            "your responsibilities",
            "role",
        ],

        "education": [
            "education",
            "education requirements",
            "educational requirements",
            "academic requirements",
            "academic qualifications",
            "educational qualifications",
            "degree requirements",
            "qualification",
            "qualifications",
        ],

        "experience": [
            "experience",
            "experience requirements",
            "work experience",
            "required experience",
            "professional experience",
            "relevant experience",
            "years of experience",
        ],

        "location": [
            "location",
            "job location",
            "work location",
            "office location",
            "job locations",
            "locations",
        ],

        "about_role": [
            "about the role",
            "about this role",
            "about the job",
            "job description",
            "description",
            "overview",
            "role overview",
            "position overview",
            "about us",
        ],
    }

    # ------------------------------------------------------------------
    # Soft skills
    # ------------------------------------------------------------------

    SOFT_SKILL_ALIASES = {
        "Analytical Thinking": [
            r"\banalytical thinking\b",
            r"\banalytical skills\b",
            r"\banalytical mindset\b",
            r"\bstrong analytical\b",
        ],

        "Problem Solving": [
            r"\bproblem solving\b",
            r"\bproblem-solving\b",
            r"\bsolve problems\b",
        ],

        "Communication": [
            r"\bcommunication\b",
            r"\bcommunicate\b",
            r"\bcommunicating\b",
            r"\bcommunication skills\b",
        ],

        "Teamwork": [
            r"\bteamwork\b",
            r"\bteam player\b",
            r"\bteam-player\b",
        ],

        "Collaboration": [
            r"\bcollaboration\b",
            r"\bcollaborate\b",
            r"\bcollaborating\b",
            r"\bcollaborative\b",
        ],

        "Leadership": [
            r"\bleadership\b",
            r"\bleading\b",
            r"\bleader\b",
        ],

        "Time Management": [
            r"\btime management\b",
            r"\bmanage time\b",
        ],

        "Critical Thinking": [
            r"\bcritical thinking\b",
            r"\bcritically think\b",
        ],

        "Adaptability": [
            r"\badaptability\b",
            r"\badaptable\b",
            r"\bflexibility\b",
            r"\bflexible\b",
        ],

        "Attention to Detail": [
            r"\battention to detail\b",
            r"\bdetail-oriented\b",
            r"\bdetail oriented\b",
        ],
    }

    # ------------------------------------------------------------------
    # Cue phrases
    # ------------------------------------------------------------------

    REQUIRED_CUES = [
        "must have",
        "must-have",
        "required",
        "requires",
        "requirement",
        "requirements",
        "minimum",
        "we are looking for",
        "we're looking for",
        "what we are looking for",
        "what we're looking for",
        "candidate must",
        "candidate should have",
        "strong knowledge",
        "strong understanding",
        "proficiency in",
        "proficient in",
        "experience with",
        "experience in",
        "knowledge of",
        "knowledge in",
        "familiarity with",
        "skills in",
    ]

    PREFERRED_CUES = [
        "preferred",
        "preferably",
        "nice to have",
        "nice-to-have",
        "good to have",
        "desired",
        "bonus",
        "plus",
        "would be a plus",
        "additional",
    ]

    RESPONSIBILITY_CUES = [
        "responsibilities",
        "responsible for",
        "you will",
        "you'll",
        "your role",
        "you would",
        "duties include",
        "will be responsible",
    ]

    ACTION_VERBS = {
        "analyze",
        "analyse",
        "build",
        "develop",
        "design",
        "create",
        "implement",
        "maintain",
        "manage",
        "monitor",
        "evaluate",
        "test",
        "deploy",
        "document",
        "support",
        "research",
        "present",
        "communicate",
        "collaborate",
        "work",
        "assist",
        "prepare",
        "generate",
        "visualize",
        "visualise",
        "interpret",
        "clean",
        "process",
        "extract",
        "report",
        "track",
        "identify",
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> Dict:
        if not text or not text.strip():
            raise ValueError(
                "Job description cannot be empty."
            )

        cleaned_text = self._clean_text(text)
        sections = self._extract_sections(
            cleaned_text
        )

        profile = create_empty_job_profile()

        profile["job_title"] = (
            self._extract_job_title(
                cleaned_text
            )
        )

        # --------------------------------------------------------------
        # Required skills
        # --------------------------------------------------------------

        required_text = sections.get(
            "required_skills",
            ""
        )

        if required_text:
            profile["required_skills"] = (
                self._extract_skills(
                    required_text
                )
            )
        else:
            required_text = (
                self._infer_required_skill_text(
                    cleaned_text
                )
            )

            profile["required_skills"] = (
                self._extract_skills(
                    required_text
                )
            )

        # --------------------------------------------------------------
        # Preferred skills
        # --------------------------------------------------------------

        preferred_text = sections.get(
            "preferred_skills",
            ""
        )

        if preferred_text:
            profile["preferred_skills"] = (
                self._extract_skills(
                    preferred_text
                )
            )
        else:
            preferred_text = (
                self._infer_preferred_skill_text(
                    cleaned_text
                )
            )

            profile["preferred_skills"] = (
                self._extract_skills(
                    preferred_text
                )
            )

        # A preferred skill should not remain required.
        profile["required_skills"] = [
            skill
            for skill in profile["required_skills"]
            if skill not in profile["preferred_skills"]
        ]

        # --------------------------------------------------------------
        # Soft skills
        # --------------------------------------------------------------

        profile["soft_skills"] = (
            self._extract_soft_skills(
                cleaned_text
            )
        )

        # --------------------------------------------------------------
        # Responsibilities
        # --------------------------------------------------------------

        responsibility_text = sections.get(
            "responsibilities",
            ""
        )

        if responsibility_text:
            profile["responsibilities"] = (
                self._extract_list(
                    responsibility_text
                )
            )
        else:
            profile["responsibilities"] = (
                self._infer_responsibilities(
                    cleaned_text
                )
            )

        # --------------------------------------------------------------
        # Education
        # --------------------------------------------------------------

        education_text = sections.get(
            "education",
            ""
        )

        if education_text:
            profile["education_requirements"] = (
                self._extract_list(
                    education_text
                )
            )
        else:
            profile["education_requirements"] = (
                self._infer_education_requirements(
                    cleaned_text
                )
            )

        # --------------------------------------------------------------
        # Experience
        # --------------------------------------------------------------

        experience_text = sections.get(
            "experience",
            ""
        )

        if experience_text:
            profile["experience_requirements"] = (
                self._extract_list(
                    experience_text
                )
            )
        else:
            profile["experience_requirements"] = (
                self._infer_experience_requirements(
                    cleaned_text
                )
            )

        # --------------------------------------------------------------
        # Location
        # --------------------------------------------------------------

        location_text = sections.get(
            "location",
            ""
        )

        if location_text:
            profile["location"] = (
                location_text.strip()
            )
        else:
            profile["location"] = (
                self._infer_location(
                    cleaned_text
                )
            )

        return profile

    # ------------------------------------------------------------------
    # Text cleaning
    # ------------------------------------------------------------------

    def _clean_text(
        self,
        text: str
    ) -> str:
        """
        Clean whitespace while preserving paragraph boundaries.

        Wrapped lines inside one paragraph are joined together.
        Separate paragraphs remain separate.
        """

        text = text.replace(
            "\r\n",
            "\n"
        )

        text = text.replace(
            "\r",
            "\n"
        )

        paragraphs = []
        current_lines = []

        for raw_line in text.split("\n"):

            line = re.sub(
                r"[ \t]+",
                " ",
                raw_line
            ).strip()

            if not line:

                if current_lines:
                    paragraphs.append(
                        " ".join(
                            current_lines
                        )
                    )

                    current_lines = []

                continue

            current_lines.append(line)

        if current_lines:
            paragraphs.append(
                " ".join(
                    current_lines
                )
            )

        return "\n".join(
            paragraphs
        )

    # ------------------------------------------------------------------
    # Section extraction
    # ------------------------------------------------------------------

    def _extract_sections(
        self,
        text: str
    ) -> Dict[str, str]:

        lines = text.split("\n")

        sections: Dict[
            str,
            List[str]
        ] = {}

        current_section: Optional[
            str
        ] = None

        alias_lookup = {}

        for (
            section_name,
            aliases
        ) in self.SECTION_ALIASES.items():

            for alias in aliases:

                alias_lookup[
                    self._normalize_heading(
                        alias
                    )
                ] = section_name

        for line in lines:

            normalized = (
                self._normalize_heading(
                    line
                )
            )

            if normalized in alias_lookup:

                current_section = (
                    alias_lookup[
                        normalized
                    ]
                )

                sections.setdefault(
                    current_section,
                    []
                )

                continue

            if current_section:
                sections[
                    current_section
                ].append(line)

        return {
            section_name: "\n".join(
                values
            ).strip()
            for (
                section_name,
                values
            ) in sections.items()
            if values
        }

    # ------------------------------------------------------------------
    # Job title
    # ------------------------------------------------------------------

    def _extract_job_title(
        self,
        text: str
    ) -> str:

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        ignored = {
            self._normalize_heading(
                alias
            )
            for aliases in (
                self.SECTION_ALIASES.values()
            )
            for alias in aliases
        }

        generic_titles = {
            "job description",
            "description",
            "overview",
            "about us",
            "requirements",
            "responsibilities",
            "qualifications",
        }

        for line in lines[:10]:

            normalized = (
                self._normalize_heading(
                    line
                )
            )

            if normalized in ignored:
                continue

            if normalized in generic_titles:
                continue

            if self._looks_like_url(line):
                continue

            if len(line) > 100:
                continue

            if self._looks_like_sentence(line):
                continue

            return line

        title_keywords = [
            "intern",
            "analyst",
            "engineer",
            "developer",
            "scientist",
            "manager",
            "designer",
            "consultant",
            "specialist",
        ]

        for line in lines[:20]:

            lower = line.lower()

            if any(
                keyword in lower
                for keyword in title_keywords
            ):

                if len(line) <= 100:
                    return line

        return ""

    # ------------------------------------------------------------------
    # Required skill inference
    # ------------------------------------------------------------------

    def _infer_required_skill_text(
        self,
        text: str
    ) -> str:
        """
        Infer required skills from an unstructured JD.

        Logical paragraphs are preserved so wrapped lines such as:

            We are looking for Python,
            SQL and Pandas knowledge.

        are treated as one requirement.
        """

        paragraphs = text.split("\n")

        selected = []

        for paragraph in paragraphs:

            lower = (
                paragraph.lower().strip()
            )

            if not lower:
                continue

            if self._is_preferred_line(
                lower
            ):
                continue

            if self._contains_any(
                lower,
                self.RESPONSIBILITY_CUES
            ):
                continue

            if self._is_education_line(
                lower
            ):
                continue

            if self._contains_any(
                lower,
                self.REQUIRED_CUES
            ):
                selected.append(
                    paragraph
                )

        return "\n".join(
            selected
        )

    # ------------------------------------------------------------------
    # Preferred skill inference
    # ------------------------------------------------------------------

    def _infer_preferred_skill_text(
        self,
        text: str
    ) -> str:

        selected = []

        for paragraph in text.split("\n"):

            lower = (
                paragraph.lower().strip()
            )

            if not lower:
                continue

            if self._is_preferred_line(
                lower
            ):
                selected.append(
                    paragraph
                )

        return "\n".join(
            selected
        )

    # ------------------------------------------------------------------
    # Skill extraction
    # ------------------------------------------------------------------

    def _extract_skills(
        self,
        text: str
    ) -> List[str]:

        if not text:
            return []

        found = []

        for (
            skill,
            patterns
        ) in self.SKILL_DICTIONARY.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                ):

                    found.append(skill)

                    break

        return (
            self._deduplicate_preserve_order(
                found
            )
        )

    # ------------------------------------------------------------------
    # Soft skills
    # ------------------------------------------------------------------

    def _extract_soft_skills(
        self,
        text: str
    ) -> List[str]:

        found = []

        for (
            skill,
            patterns
        ) in self.SOFT_SKILL_ALIASES.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                ):

                    found.append(skill)

                    break

        return (
            self._deduplicate_preserve_order(
                found
            )
        )

    # ------------------------------------------------------------------
    # Responsibilities
    # ------------------------------------------------------------------

    def _infer_responsibilities(
        self,
        text: str
    ) -> List[str]:

        responsibilities = []

        for paragraph in text.split("\n"):

            line = paragraph.strip()

            if not line:
                continue

            lower = line.lower()

            if self._is_preferred_line(
                lower
            ):
                continue

            if self._contains_any(
                lower,
                self.RESPONSIBILITY_CUES
            ):

                responsibilities.append(
                    line
                )

                continue

            if self._looks_like_action_bullet(
                line
            ):

                responsibilities.append(
                    line
                )

        return (
            self._deduplicate_preserve_order(
                responsibilities
            )
        )

    def _looks_like_action_bullet(
        self,
        line: str
    ) -> bool:

        cleaned = re.sub(
            r"^[\-\*\u2022\d\.\)\s]+",
            "",
            line
        ).strip()

        if not cleaned:
            return False

        match = re.match(
            r"([A-Za-z]+)",
            cleaned
        )

        if not match:
            return False

        first_word = (
            match.group(1).lower()
        )

        return (
            first_word
            in self.ACTION_VERBS
        )

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    def _is_education_line(
        self,
        line: str
    ) -> bool:

        education_keywords = [
            "bachelor",
            "master",
            "b.tech",
            "btech",
            "b.e",
            "b.sc",
            "m.tech",
            "mtech",
            "m.sc",
            "degree",
            "computer science",
            "data science",
            "statistics",
            "mathematics",
            "engineering degree",
        ]

        return self._contains_any(
            line.lower(),
            education_keywords
        )

    def _infer_education_requirements(
        self,
        text: str
    ) -> List[str]:

        result = []

        for line in text.split("\n"):

            if self._is_education_line(
                line
            ):

                result.append(
                    line.strip()
                )

        return (
            self._deduplicate_preserve_order(
                result
            )
        )

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    def _infer_experience_requirements(
        self,
        text: str
    ) -> List[str]:

        result = []

        explicit_patterns = [
            r"\b\d+\+?\s*(?:years?|yrs?)\s+of\s+experience\b",
            r"\bexperience\s+(?:with|in)\b",
            r"\bprevious\s+(?:internship|work)\s+experience\b",
            r"\bprior\s+(?:internship|work)\s+experience\b",
            r"\binternship\s+experience\b",
            r"\bwork\s+experience\b",
            r"\bprofessional\s+experience\b",
            r"\brelevant\s+experience\b",
        ]

        for line in text.split("\n"):

            lower = line.lower()

            if self._is_preferred_line(
                lower
            ):
                continue

            if any(
                re.search(
                    pattern,
                    lower
                )
                for pattern in explicit_patterns
            ):

                result.append(
                    line.strip()
                )

        return (
            self._deduplicate_preserve_order(
                result
            )
        )

    # ------------------------------------------------------------------
    # Location
    # ------------------------------------------------------------------

    def _infer_location(
        self,
        text: str
    ) -> str:

        known_locations = [
            "Hyderabad",
            "Bengaluru",
            "Bangalore",
            "Chennai",
            "Mumbai",
            "Pune",
            "Delhi",
            "Gurugram",
            "Gurgaon",
            "Noida",
            "Kolkata",
            "Remote",
            "Hybrid",
            "India",
            "United States",
            "USA",
            "United Kingdom",
            "UK",
        ]

        for line in text.split("\n"):

            lower = line.lower()

            if any(
                location.lower() in lower
                for location in known_locations
            ):

                return line.strip()

        return ""

    # ------------------------------------------------------------------
    # List extraction
    # ------------------------------------------------------------------

    def _extract_list(
        self,
        text: str
    ) -> List[str]:

        if not text:
            return []

        items = []
        current = ""

        for raw_line in text.split("\n"):

            line = raw_line.strip()

            if not line:
                continue

            is_bullet = bool(
                re.match(
                    r"^[-*•]\s+",
                    line
                )
                or re.match(
                    r"^\d+[\.\)]\s+",
                    line
                )
            )

            if is_bullet:

                if current:
                    items.append(
                        current.strip()
                    )

                current = re.sub(
                    r"^[-*•]\s+",
                    "",
                    line
                )

                current = re.sub(
                    r"^\d+[\.\)]\s+",
                    "",
                    current
                )

            else:

                if current:
                    current += " " + line

                else:
                    current = line

        if current:
            items.append(
                current.strip()
            )

        return (
            self._deduplicate_preserve_order(
                items
            )
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_heading(
        self,
        text: str
    ) -> str:

        text = text.lower().strip()

        text = re.sub(
            r"[:\-]+$",
            "",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    def _contains_any(
        self,
        text: str,
        phrases: List[str]
    ) -> bool:

        return any(
            phrase.lower() in text
            for phrase in phrases
        )

    def _is_preferred_line(
        self,
        lower_line: str
    ) -> bool:

        return self._contains_any(
            lower_line,
            self.PREFERRED_CUES
        )

    def _looks_like_url(
        self,
        text: str
    ) -> bool:

        return bool(
            re.search(
                r"(https?://|www\.|\.com\b|\.org\b|\.in\b)",
                text,
                flags=re.IGNORECASE
            )
        )

    def _looks_like_sentence(
        self,
        text: str
    ) -> bool:

        words = text.split()

        if len(words) > 12:
            return True

        if text.endswith("."):
            return True

        sentence_starters = {
            "we",
            "the",
            "you",
            "candidate",
            "this",
            "our",
            "a",
            "an",
        }

        if (
            words
            and words[0].lower()
            in sentence_starters
        ):
            return True

        return False

    def _deduplicate_preserve_order(
        self,
        values: List[str]
    ) -> List[str]:

        seen = set()
        result = []

        for value in values:

            key = value.lower().strip()

            if key not in seen:

                seen.add(key)
                result.append(value)

        return result


# ----------------------------------------------------------------------
# Backward-compatible alias
# ----------------------------------------------------------------------

JobDescriptionAnalyzer = JobAnalyzer