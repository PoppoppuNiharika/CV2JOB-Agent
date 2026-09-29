from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# =========================================================
# BACKEND IMPORTS
# =========================================================

from parser import DocumentParser  # noqa: E402
from cv_analyzer import CVAnalyzer  # noqa: E402
from job_analyzer import JobAnalyzer  # noqa: E402
from integrated_matcher import IntegratedMatcher  # noqa: E402
from gap_analyzer import GapAnalyzer  # noqa: E402
from improvement_planner import ImprovementPlanner  # noqa: E402
from report_generator import ReportGenerator  # noqa: E402


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CV2JOB-Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
    <style>
        .main { padding-top: 1rem; }
        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(128,128,128,.20);
            background: linear-gradient(
                135deg,
                rgba(255,214,10,.18),
                rgba(147,51,234,.14)
            );
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: .4rem;
        }
        .hero-subtitle {
            font-size: 1.05rem;
            opacity: .82;
        }
        .section-title {
            font-size: 1.55rem;
            font-weight: 750;
            margin-top: 1.5rem;
            margin-bottom: .8rem;
        }
        .status-card {
            border: 1px solid rgba(128,128,128,.20);
            border-radius: 16px;
            padding: 1rem;
            min-height: 130px;
        }
        .status-label {
            font-size: .9rem;
            opacity: .70;
        }
        .status-value {
            font-size: 2rem;
            font-weight: 800;
            margin-top: .25rem;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.18);
            border-radius: 14px;
            padding: .8rem;
        }
        .stButton > button {
            font-weight: 700;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# BACKEND COMPONENTS
# =========================================================

@st.cache_resource(show_spinner=False)
def get_parser() -> DocumentParser:
    return DocumentParser()


@st.cache_resource(show_spinner=False)
def get_cv_analyzer() -> CVAnalyzer:
    return CVAnalyzer()


@st.cache_resource(show_spinner=False)
def get_job_analyzer() -> JobAnalyzer:
    return JobAnalyzer()


@st.cache_resource(show_spinner=False)
def get_integrated_matcher() -> IntegratedMatcher:
    return IntegratedMatcher()


@st.cache_resource(show_spinner=False)
def get_gap_analyzer() -> GapAnalyzer:
    return GapAnalyzer()


@st.cache_resource(show_spinner=False)
def get_improvement_planner() -> ImprovementPlanner:
    return ImprovementPlanner()


@st.cache_resource(show_spinner=False)
def get_report_generator() -> ReportGenerator:
    return ReportGenerator()


# =========================================================
# INPUT / PIPELINE HELPERS
# =========================================================

def safe_uploaded_bytes(uploaded_file: Any) -> tuple[bytes, str]:
    if uploaded_file is None:
        raise ValueError("No file was uploaded.")

    file_name = getattr(uploaded_file, "name", "")
    if not file_name:
        raise ValueError("The uploaded file does not have a filename.")

    data = uploaded_file.getvalue()
    if not data:
        raise ValueError(f"{file_name} is empty.")

    return data, file_name


def analyze_cv(uploaded_cv: Any) -> dict[str, Any]:
    parser = get_parser()
    analyzer = get_cv_analyzer()

    data, file_name = safe_uploaded_bytes(uploaded_cv)
    cv_text, links = parser.parse_with_links(
        data,
        file_name=file_name,
    )

    return analyzer.analyze(
        cv_text,
        links=links,
    )


def analyze_job(
    uploaded_job: Any,
    pasted_job: str,
) -> dict[str, Any]:
    parser = get_parser()
    analyzer = get_job_analyzer()

    if uploaded_job is not None:
        data, file_name = safe_uploaded_bytes(uploaded_job)
        job_text = parser.parse(
            data,
            file_name=file_name,
        )
    else:
        job_text = pasted_job.strip()

    if not job_text:
        raise ValueError(
            "Please upload or paste a job description."
        )

    return analyzer.analyze(job_text)


def run_pipeline(
    cv_profile: dict[str, Any],
    job_profile: dict[str, Any],
) -> dict[str, Any]:
    matcher = get_integrated_matcher()
    gap_analyzer = get_gap_analyzer()
    planner = get_improvement_planner()
    generator = get_report_generator()

    integrated_result = matcher.analyze(
        cv_profile,
        job_profile,
    )

    gap_result = gap_analyzer.analyze(
        integrated_result
    )

    improvement_result = planner.create_plan(
        gap_result
    )

    report = generator.generate(
        integrated_result,
        gap_result,
        improvement_result,
    )

    return {
        "cv_profile": cv_profile,
        "job_profile": job_profile,
        "integrated_result": integrated_result,
        "gap_result": gap_result,
        "improvement_result": improvement_result,
        "report": report,
    }


# =========================================================
# DISPLAY HELPERS
# =========================================================

def status_counts(
    requirements: list[dict[str, Any]],
) -> dict[str, int]:
    counts = {
        "Confirmed Match": 0,
        "Evidence Match": 0,
        "Evidence Found": 0,
        "Potential Match": 0,
        "Gap": 0,
    }

    for item in requirements:
        status = item.get("status", "")
        if status in counts:
            counts[status] += 1

    return counts


def format_evidence(evidence: Any) -> str:
    """
    Convert evidence records to displayable text.

    EvidenceMapper stores evidence as dictionaries such as:
        {
            "source": "Projects",
            "category": "projects",
            "text": "..."
        }

    Older/other pipeline paths may provide plain strings.
    This helper supports both without allowing dicts to reach
    str.join(), which caused the Streamlit TypeError.
    """

    if evidence is None:
        return ""

    if isinstance(evidence, str):
        return evidence.strip()

    if not isinstance(evidence, list):
        return str(evidence).strip()

    parts: list[str] = []

    for item in evidence:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                parts.append(cleaned)
            continue

        if isinstance(item, dict):
            text = item.get("text", "")
            source = item.get("source", "")
            category = item.get("category", "")

            if isinstance(text, str) and text.strip():
                cleaned_text = text.strip()
                if isinstance(source, str) and source.strip():
                    cleaned_text = f"[{source.strip()}] {cleaned_text}"
                parts.append(cleaned_text)
                continue

            if isinstance(category, str) and category.strip():
                parts.append(category.strip())
                continue

            parts.append(str(item))
            continue

        parts.append(str(item))

    return "; ".join(parts)


def requirement_dataframe(
    requirements: list[dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for item in requirements:
        try:
            semantic_score = float(
                item.get("semantic_score", 0.0)
            )
        except (TypeError, ValueError):
            semantic_score = 0.0

        rows.append(
            {
                "Requirement": item.get("requirement", ""),
                "Category": item.get("category", ""),
                "Status": item.get("status", ""),
                "Confidence": item.get("confidence", ""),
                "Semantic Score": round(
                    semantic_score,
                    3,
                ),
                "Evidence": format_evidence(
                    item.get("evidence", [])
                ),
            }
        )

    return pd.DataFrame(rows)


def skills_dataframe(
    cv_profile: dict[str, Any],
) -> pd.DataFrame:
    rows = []
    skills = cv_profile.get("skills", {})

    if not isinstance(skills, dict):
        return pd.DataFrame()

    for category, values in skills.items():
        if not isinstance(values, list):
            continue

        for value in values:
            if isinstance(value, str) and value.strip():
                rows.append(
                    {
                        "Category": category.replace(
                            "_",
                            " "
                        ).title(),
                        "Skill": value,
                    }
                )

    return pd.DataFrame(rows)


def action_dataframe(
    actions: list[dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for action in actions:
        rows.append(
            {
                "Requirement": action.get(
                    "requirement",
                    "",
                ),
                "Category": action.get(
                    "category",
                    "",
                ),
                "Type": action.get(
                    "type",
                    "",
                ),
                "Priority": action.get(
                    "priority",
                    "",
                ),
                "Rationale": action.get(
                    "rationale",
                    "",
                ),
            }
        )

    return pd.DataFrame(rows)


def report_json_bytes(
    report: dict[str, Any],
) -> bytes:
    return json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🎯 CV2JOB-Agent")
    st.caption(
        "CV-to-job intelligence and improvement planning"
    )

    st.markdown("---")
    st.markdown("### Workflow")
    st.markdown(
        """
        1. Upload CV
        2. Add target JD
        3. Run analysis
        4. Review matches
        5. Inspect gaps
        6. Follow improvement plan
        """
    )

    st.markdown("---")
    st.caption(
        "Documents are processed by the application pipeline."
    )


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🎯 CV2JOB-Agent</div>
        <div class="hero-subtitle">
            Analyze how well a CV matches one target job description,
            understand the evidence behind every result, identify gaps,
            and generate a targeted improvement plan.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# INPUTS
# =========================================================

st.markdown(
    '<div class="section-title">📄 1. Upload your CV</div>',
    unsafe_allow_html=True,
)

cv_file = st.file_uploader(
    "CV / Resume",
    type=["pdf", "docx", "txt"],
    key="cv_uploader",
)

st.markdown(
    '<div class="section-title">💼 2. Add the target job description</div>',
    unsafe_allow_html=True,
)

jd_col1, jd_col2 = st.columns([1, 1])

with jd_col1:
    jd_file = st.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx", "txt"],
        key="jd_uploader",
    )

with jd_col2:
    jd_text = st.text_area(
        "Or paste Job Description",
        height=180,
        placeholder="Paste the complete target job description here...",
        key="jd_text",
    )

st.markdown("")

run_col1, run_col2, run_col3 = st.columns([2, 1, 1])

with run_col1:
    analyze_clicked = st.button(
        "🚀 Analyze CV Against Job",
        type="primary",
        use_container_width=True,
    )

with run_col2:
    if st.button(
        "🧹 Clear Results",
        use_container_width=True,
    ):
        for key in [
            "analysis_result",
            "cv_name",
            "job_title",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

with run_col3:
    st.caption("One CV + one target JD")


# =========================================================
# RUN ANALYSIS
# =========================================================

if analyze_clicked:
    if cv_file is None:
        st.error("Please upload your CV first.")
        st.stop()

    if jd_file is None and not jd_text.strip():
        st.error("Please upload or paste a job description.")
        st.stop()

    try:
        with st.status(
            "Running CV2JOB-Agent...",
            expanded=True,
        ) as status:
            st.write("📄 Parsing CV...")
            cv_profile = analyze_cv(cv_file)

            st.write("💼 Analyzing job description...")
            job_profile = analyze_job(
                jd_file,
                jd_text,
            )

            st.write("🧠 Running integrated matching...")
            pipeline_result = run_pipeline(
                cv_profile,
                job_profile,
            )

            status.update(
                label="Analysis complete",
                state="complete",
                expanded=False,
            )

        st.session_state["analysis_result"] = pipeline_result
        st.session_state["cv_name"] = cv_profile.get("name", "")
        st.session_state["job_title"] = job_profile.get("job_title", "")

        st.success(
            "CV-to-job analysis completed successfully."
        )

    except Exception as error:
        st.error(
            f"Analysis failed: {type(error).__name__}: {error}"
        )
        st.stop()


# =========================================================
# WAIT FOR RESULTS
# =========================================================

if "analysis_result" not in st.session_state:
    st.info(
        "Upload your CV and add one target job description, "
        "then click **Analyze CV Against Job**."
    )
    st.stop()


pipeline = st.session_state["analysis_result"]
cv_profile = pipeline["cv_profile"]
job_profile = pipeline["job_profile"]
integrated_result = pipeline["integrated_result"]
gap_result = pipeline["gap_result"]
report = pipeline["report"]


# =========================================================
# SUMMARY
# =========================================================

st.markdown(
    '<div class="section-title">📊 Analysis Summary</div>',
    unsafe_allow_html=True,
)

report_summary = report["match_summary"]

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Weighted Match",
        f"{report['overall_match']:.1f}%",
    )

with metric2:
    st.metric(
        "Requirement Coverage",
        f"{report['coverage']:.1f}%",
    )

with metric3:
    st.metric(
        "Confirmed",
        report_summary["confirmed_matches"],
    )

with metric4:
    st.metric(
        "Gaps",
        report_summary["gaps"],
    )


job_title = report.get("job_title", "").strip()

if job_title:
    st.markdown(f"**Target Role:** {job_title}")
else:
    st.markdown(
        "**Target Role:** Not detected from the job description"
    )


# =========================================================
# MATCH BREAKDOWN
# =========================================================

requirements = integrated_result.get("requirements", [])
counts = status_counts(requirements)

st.markdown(
    '<div class="section-title">🔎 Match Breakdown</div>',
    unsafe_allow_html=True,
)

status_cols = st.columns(5)

status_items = [
    (status_cols[0], "Confirmed", counts["Confirmed Match"]),
    (status_cols[1], "Evidence Match", counts["Evidence Match"]),
    (status_cols[2], "Potential", counts["Potential Match"]),
    (status_cols[3], "Evidence Found", counts["Evidence Found"]),
    (status_cols[4], "Gap", counts["Gap"]),
]

for column, label, value in status_items:
    with column:
        st.markdown(
            f"""
            <div class="status-card">
                <div class="status-label">{label}</div>
                <div class="status-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# TABS
# =========================================================

(
    tab_overview,
    tab_requirements,
    tab_gaps,
    tab_plan,
    tab_cv,
    tab_job,
) = st.tabs(
    [
        "🏠 Overview",
        "🔍 Requirements",
        "🚨 Gaps",
        "🛠 Improvement Plan",
        "👤 CV Profile",
        "💼 Job Profile",
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

with tab_overview:
    st.markdown("### What this analysis means")
    st.write(
        "The weighted match is the deterministic compatibility score "
        "produced by the matching layer. Requirement coverage shows "
        "how many target requirements were resolved by the integrated "
        "matching system."
    )

    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### Match counts")
        overview_df = pd.DataFrame(
            [
                {"Status": "Confirmed Match", "Count": counts["Confirmed Match"]},
                {"Status": "Evidence Match", "Count": counts["Evidence Match"]},
                {"Status": "Potential Match", "Count": counts["Potential Match"]},
                {"Status": "Evidence Found", "Count": counts["Evidence Found"]},
                {"Status": "Gap", "Count": counts["Gap"]},
            ]
        )
        st.bar_chart(overview_df.set_index("Status"))

    with right:
        st.markdown("#### Priority summary")
        gap_summary = gap_result.get("summary", {})
        priority_df = pd.DataFrame(
            [
                {
                    "Priority": "High",
                    "Count": gap_summary.get("high_priority_gaps", 0),
                },
                {
                    "Priority": "Medium",
                    "Count": gap_summary.get("medium_priority_gaps", 0),
                },
                {
                    "Priority": "Low",
                    "Count": gap_summary.get("low_priority_gaps", 0),
                },
            ]
        )
        st.bar_chart(priority_df.set_index("Priority"))

    st.download_button(
        label="⬇️ Download Analysis Report (JSON)",
        data=report_json_bytes(report),
        file_name="cv2job_analysis_report.json",
        mime="application/json",
        use_container_width=True,
    )


# =========================================================
# REQUIREMENTS
# =========================================================

with tab_requirements:
    st.markdown("### Requirement-by-requirement analysis")

    if not requirements:
        st.info("No requirements were detected.")
    else:
        df = requirement_dataframe(requirements)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Detailed evidence")

        for index, item in enumerate(requirements, start=1):
            requirement = item.get("requirement", "")
            status = item.get("status", "")
            confidence = item.get("confidence", "")

            with st.expander(
                f"{index}. {requirement} — {status}"
            ):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(
                        f"**Category:** {item.get('category', '')}"
                    )

                with col2:
                    st.write(
                        f"**Confidence:** {confidence}"
                    )

                with col3:
                    try:
                        score = float(
                            item.get(
                                "semantic_score",
                                0.0,
                            )
                        )
                    except (TypeError, ValueError):
                        score = 0.0

                    st.write(
                        f"**Semantic Score:** {score:.3f}"
                    )

                evidence = item.get("evidence", [])

                if evidence:
                    st.markdown("**Explicit CV evidence**")
                    if isinstance(evidence, list):
                        for evidence_item in evidence:
                            if isinstance(evidence_item, dict):
                                text = evidence_item.get("text", "")
                                source = evidence_item.get("source", "")
                                if text:
                                    if source:
                                        st.write(
                                            f"- **{source}:** {text}"
                                        )
                                    else:
                                        st.write(f"- {text}")
                            else:
                                st.write(f"- {evidence_item}")
                    else:
                        st.write(f"- {evidence}")
                else:
                    st.caption(
                        "No explicit CV evidence was mapped."
                    )

                best_semantic = item.get(
                    "best_semantic_evidence",
                    "",
                )

                if best_semantic:
                    st.markdown("**Best semantic evidence**")
                    st.write(best_semantic)

                st.caption(
                    "Semantic similarity indicates relatedness; it is "
                    "not treated as proof of possessing a skill."
                )


# =========================================================
# GAPS
# =========================================================

with tab_gaps:
    st.markdown("### Missing requirements")

    gaps = report.get("gaps", [])

    if not gaps:
        st.success("No requirement gaps were identified.")
    else:
        for index, gap in enumerate(gaps, start=1):
            with st.expander(
                f"{index}. {gap.get('requirement', '')} — "
                f"{gap.get('priority', 'Low')}"
            ):
                st.write(
                    f"**Category:** {gap.get('category', '')}"
                )
                st.write(
                    f"**Reason:** {gap.get('reason', '')}"
                )
                if gap.get("suggested_action"):
                    st.write(
                        f"**Suggested action:** "
                        f"{gap['suggested_action']}"
                    )

    st.markdown("### Evidence that should be strengthened")

    evidence_improvements = report.get(
        "evidence_improvements",
        [],
    )

    if not evidence_improvements:
        st.success(
            "No additional evidence improvements were identified."
        )
    else:
        for item in evidence_improvements:
            st.info(
                f"**{item.get('requirement', '')}** — "
                f"{item.get('priority', 'Low')} priority\n\n"
                f"{item.get('reason', '')}"
            )


# =========================================================
# IMPROVEMENT PLAN
# =========================================================

with tab_plan:
    st.markdown("### Targeted improvement plan")

    action_plan = report.get("improvement_plan", [])
    improvement_summary = report.get(
        "improvement_summary",
        {},
    )

    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.metric(
            "Total Actions",
            improvement_summary.get(
                "total_actions",
                len(action_plan),
            ),
        )

    with p2:
        st.metric(
            "High Priority",
            improvement_summary.get(
                "high_priority_actions",
                0,
            ),
        )

    with p3:
        st.metric(
            "Medium Priority",
            improvement_summary.get(
                "medium_priority_actions",
                0,
            ),
        )

    with p4:
        st.metric(
            "Low Priority",
            improvement_summary.get(
                "low_priority_actions",
                0,
            ),
        )

    if action_plan:
        action_df = action_dataframe(action_plan)
        st.dataframe(
            action_df,
            use_container_width=True,
            hide_index=True,
        )

        for index, action in enumerate(action_plan, start=1):
            with st.expander(
                f"{index}. {action.get('requirement', '')} — "
                f"{action.get('type', '')}"
            ):
                st.write(
                    f"**Category:** {action.get('category', '')}"
                )
                st.write(
                    f"**Priority:** {action.get('priority', '')}"
                )
                st.write(
                    f"**Rationale:** {action.get('rationale', '')}"
                )

                st.markdown("**Steps**")
                for step_number, step in enumerate(
                    action.get("steps", []),
                    start=1,
                ):
                    st.write(
                        f"{step_number}. {step}"
                    )
    else:
        st.success(
            "No improvement actions are currently required."
        )


# =========================================================
# CV PROFILE
# =========================================================

with tab_cv:
    st.markdown("### Extracted candidate profile")

    name = cv_profile.get("name", "")
    contact = cv_profile.get("contact", {})

    st.write(
        f"**Name:** {name or 'Not detected'}"
    )

    if isinstance(contact, dict):
        c1, c2 = st.columns(2)

        with c1:
            st.write(
                f"**Email:** {contact.get('email', '') or 'Not detected'}"
            )
            st.write(
                f"**Phone:** {contact.get('phone', '') or 'Not detected'}"
            )

        with c2:
            linkedin = contact.get("linkedin", "")
            github = contact.get("github", "")

            if linkedin:
                st.markdown(
                    f"**LinkedIn:** [{linkedin}]({linkedin})"
                )
            else:
                st.write("**LinkedIn:** Not detected")

            if github:
                st.markdown(
                    f"**GitHub:** [{github}]({github})"
                )
            else:
                st.write("**GitHub:** Not detected")

    st.markdown("### Skills")
    cv_skills_df = skills_dataframe(cv_profile)

    if not cv_skills_df.empty:
        st.dataframe(
            cv_skills_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No structured skills detected.")

    for title, key in [
        ("Education", "education"),
        ("Experience", "experience"),
        ("Projects", "projects"),
        ("Certifications", "certifications"),
        ("Activities", "activities"),
    ]:
        st.markdown(f"### {title}")
        values = cv_profile.get(key, [])
        if values:
            for item in values:
                st.write(f"- {item}")
        else:
            st.caption("None detected.")

    with st.expander("View extracted CV text"):
        st.text(
            cv_profile.get(
                "raw_text",
                "",
            )
        )


# =========================================================
# JOB PROFILE
# =========================================================

with tab_job:
    st.markdown("### Extracted job profile")

    detected_title = job_profile.get(
        "job_title",
        "",
    )

    st.write(
        f"**Job Title:** {detected_title or 'Not detected'}"
    )

    st.write(
        f"**Location:** "
        f"{job_profile.get('location', '') or 'Not detected'}"
    )

    job_sections = [
        ("Required Skills", "required_skills"),
        ("Preferred Skills", "preferred_skills"),
        ("Soft Skills", "soft_skills"),
        ("Responsibilities", "responsibilities"),
        ("Education Requirements", "education_requirements"),
        ("Experience Requirements", "experience_requirements"),
    ]

    for title, key in job_sections:
        st.markdown(f"#### {title}")
        values = job_profile.get(key, [])

        if values:
            for value in values:
                st.write(f"- {value}")
        else:
            st.caption("None detected.")

    with st.expander("View extracted job description"):
        st.text(
            job_profile.get(
                "raw_text",
                "",
            )
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")
st.caption(
    "CV2JOB-Agent | Document Parsing → CV Analysis → JD Analysis "
    "→ Deterministic Matching → Evidence Mapping → Semantic Matching "
    "→ Gap Analysis → Improvement Planning → Final Report"
)
