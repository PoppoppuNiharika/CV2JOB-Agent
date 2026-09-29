# CV2JOB-Agent

> An intelligent CV-to-Job matching and career improvement system that analyzes a candidate's CV against a target Job Description, maps evidence to requirements, identifies gaps, and generates a targeted improvement plan.

---

## 🚀 Overview

CV2JOB-Agent is an AI-assisted CV-to-Job analysis system designed to help students and job seekers understand how well their existing profile aligns with a target job description.

Instead of performing only keyword matching, the system combines:

- Document parsing
- CV structure analysis
- Job description analysis
- Deterministic skill matching
- Evidence mapping
- Semantic similarity matching
- Integrated requirement evaluation
- Gap analysis
- Improvement planning
- Structured report generation

The final results are presented through an interactive Streamlit web application.

---

## 🎯 Problem Statement

Students and job seekers often have difficulty understanding:

- Which skills a job actually requires
- Which requirements are already supported by their CV
- Which requirements are only partially supported
- Which skills are missing
- Whether their CV contains sufficient evidence for a skill
- What they should improve before applying

Traditional keyword-based resume screening can miss related evidence and meaningful semantic relationships.

CV2JOB-Agent addresses this by combining deterministic matching with evidence-based and semantic analysis.

---

# 💡 Solution

The system accepts two primary inputs:

1. **Candidate CV**
2. **Target Job Description**

It processes both documents independently and then compares the extracted requirements against the candidate's profile.

The system produces:

- Requirement-level matches
- Evidence supporting each requirement
- Semantic similarity information
- Skill gaps
- Evidence improvement areas
- Priorities
- Actionable improvement recommendations
- Overall compatibility metrics

---

# 🧠 System Architecture

```text
                    CV + Job Description
                            │
                            ▼
                    Document Parser
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        CV Analyzer                 JD Analyzer
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    Deterministic Matcher
                            │
                            ▼
                    Evidence Mapper
                            │
                            ▼
                    Semantic Matcher
                            │
                            ▼
                   Integrated Matcher
                            │
                            ▼
                      Gap Analyzer
                            │
                            ▼
                  Improvement Planner
                            │
                            ▼
                    Report Generator
                            │
                            ▼
                     Streamlit UI
```

---

# 🔄 End-to-End Workflow

## 1. Document Parsing

The system first extracts text from the uploaded documents.

Supported formats include:

- PDF
- DOCX
- TXT

The parser also supports:

- File paths
- Byte content
- File-like objects
- Streamlit uploaded files

The parser handles document-specific extraction and preserves relevant document structure.

---

## 2. CV Analysis

The CV analyzer extracts structured candidate information such as:

- Contact information
- Education
- Skills
- Experience
- Projects
- Certifications
- Activities
- Links
- Other relevant profile information

The analyzer also identifies skills mentioned inside experience, projects, certifications, and other evidence sections.

This prevents the system from relying only on a dedicated "Skills" section.

---

## 3. Job Description Analysis

The Job Description analyzer extracts:

- Required skills
- Preferred skills
- Soft skills
- Responsibilities
- Education requirements
- Experience requirements
- Location
- Role information

The analyzer can also infer relevant sections when a job description does not contain clearly defined headings.

---

# 🔎 4. Deterministic Matching

The deterministic matcher performs explicit requirement-to-CV matching.

It checks whether requirements such as:

```text
Python
SQL
Pandas
NumPy
Power BI
Git
```

are explicitly supported by the candidate profile.

The system separately evaluates:

- Required skills
- Preferred skills
- Soft skills

The weighted compatibility calculation uses:

```text
Required Skills  → 70%
Preferred Skills → 20%
Soft Skills      → 10%
```

Only requirement groups that contain actual requirements contribute to the denominator.

The resulting score represents **profile-to-requirement compatibility**, not hiring probability.

---

# 📌 5. Evidence Mapping

A requirement being mentioned in a CV is not always enough.

CV2JOB-Agent therefore maps requirements to supporting CV evidence.

Evidence can come from:

- Technical Skills
- Core Strengths
- Experience
- Projects
- Certifications
- Activities

For example:

```text
Requirement:
Data Analysis

Evidence:
ShadowFox Data Science Internship
Delhi AQI analysis project
Python/Pandas/NumPy based analysis
```

The evidence mapper also removes duplicate evidence and limits excessive repetition.

---

# 🤖 6. Semantic Matching

The semantic matcher adds an NLP-based layer on top of exact matching.

It uses a Sentence Transformer model:

```text
all-MiniLM-L6-v2
```

The model converts requirements and candidate evidence into embeddings and compares their semantic similarity.

Similarity interpretation:

| Similarity | Interpretation |
|---|---|
| ≥ 0.70 | Strong |
| ≥ 0.50 | Related |
| ≥ 0.35 | Weak |
| < 0.35 | No Meaningful |

Semantic similarity is treated as supporting evidence rather than absolute proof of a skill.

---

# 🧩 7. Integrated Matching

The integrated matcher combines:

- Deterministic matching
- Evidence mapping
- Semantic matching

Each requirement receives a more meaningful status.

Possible statuses include:

```text
Confirmed Match
Evidence Match
Evidence Found
Potential Match
Gap
```

### Confirmed Match

The requirement is explicitly supported by the candidate profile.

### Evidence Match

Explicit evidence exists and semantic similarity also supports the relationship.

### Evidence Found

Relevant explicit evidence exists, but the semantic relationship is weaker.

### Potential Match

Semantic evidence suggests a possible relationship even without strong explicit evidence.

### Gap

The available CV evidence does not sufficiently support the requirement.

---

# 🚨 8. Gap Analysis

The gap analyzer converts matching results into actionable gaps.

It distinguishes between:

### Actual Skill Gaps

The candidate has insufficient evidence for the requirement.

Example:

```text
Machine Learning
Scikit-learn
```

### Evidence Improvement Areas

The candidate may already have relevant experience, but the CV does not communicate it clearly enough.

Example:

```text
Data Analysis
Data Visualization
```

This distinction is important because a candidate should not unnecessarily relearn a skill they already demonstrate.

---

# 🛠️ 9. Improvement Planning

The improvement planner converts identified gaps into actionable recommendations.

Each recommendation can include:

- Skill
- Category
- Priority
- Rationale
- Action steps

Examples of improvement categories include:

```text
Optional Skill Development
Evidence Development
Evidence Improvement
```

For evidence improvement, the system focuses on making the existing CV evidence clearer rather than assuming the candidate needs to learn the skill from scratch.

---

# 📊 10. Report Generation

The report generator combines the results from the complete analysis pipeline.

The generated report includes:

- Target role
- Weighted compatibility score
- Requirement coverage
- Confirmed matches
- Evidence matches
- Potential matches
- Evidence found
- Gaps
- Improvement actions

---

# 🖥️ Streamlit Application

The project provides an interactive Streamlit interface.

The application is organized into the following sections:

### 🏠 Overview

Provides a high-level summary of the analysis.

### 🔍 Requirements

Displays job requirements and their matching status.

### 🚨 Gaps

Displays identified skill and evidence gaps.

### 🛠️ Improvement Plan

Displays recommended actions for improving alignment with the target role.

### 👤 CV Profile

Displays the structured candidate profile extracted from the CV.

### 💼 Job Profile

Displays the structured information extracted from the target job description.

---

# ✨ Key Features

- 📄 PDF CV parsing
- 📝 DOCX parsing
- 📃 TXT parsing
- 🧠 Structured CV analysis
- 💼 Job description analysis
- 🔎 Required/preferred skill identification
- 🎯 Deterministic requirement matching
- 📌 Evidence mapping
- 🤖 Semantic similarity matching
- 🔗 Integrated matching
- 🚨 Gap identification
- 🛠️ Personalized improvement planning
- 📊 Structured reporting
- 🖥️ Interactive Streamlit UI
- 🧪 Automated backend test suite

---

# 🧰 Technology Stack

## Programming Language

- Python

## Frontend / Application

- Streamlit

## Data Processing

- Pandas
- NumPy

## Machine Learning / NLP

- Scikit-learn
- Sentence Transformers
- Transformers
- PyTorch

## Document Processing

- PyMuPDF
- python-docx

## Visualization

- Plotly

## Testing

- Pytest

## Development Tools

- VS Code
- Git
- GitHub

---

# 📁 Project Structure

```text
CV2JOB-Agent/
│
├── README.md
├── app.py
├── requirements.txt
├── test_job_description.txt
├── .gitignore
│
└── src/
    │
    ├── models.py
    │
    ├── parser.py
    ├── test_parser.py
    │
    ├── cv_analyzer.py
    ├── test_cv_analyzer.py
    │
    ├── job_analyzer.py
    ├── test_job_analyzer.py
    │
    ├── matcher.py
    ├── test_matcher.py
    │
    ├── evidence_mapper.py
    ├── test_evidence_mapper.py
    │
    ├── semantic_matcher.py
    ├── test_semantic_matcher.py
    │
    ├── integrated_matcher.py
    ├── test_integrated_matcher.py
    │
    ├── gap_analyzer.py
    ├── test_gap_analyzer.py
    │
    ├── improvement_planner.py
    ├── test_improvement_planner.py
    │
    ├── report_generator.py
    └── test_report_generator.py
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CV2JOB-Agent
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

## 3. Activate the environment

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

## 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

# ▶️ Running the Application

Start the Streamlit application with:

```bash
python -m streamlit run app.py
```

The application will open in your browser.

---

# 🧪 Running Tests

The complete backend test suite can be executed using:

```bash
python -m pytest src -q --cache-clear
```

Current verified result:

```text
142 passed
```

The tests cover the major backend components including:

- Document parsing
- CV analysis
- Job analysis
- Deterministic matching
- Evidence mapping
- Semantic matching
- Integrated matching
- Gap analysis
- Improvement planning
- Report generation

---

# 📈 Example Analysis

For a Data Analyst Intern role, the system can identify requirements such as:

```text
Python
SQL
Pandas
NumPy
Data Analysis
Data Visualization
Microsoft Excel
Power BI
Streamlit
Scikit-learn
Machine Learning
Communication
Collaboration
```

The system then determines whether each requirement is:

```text
Confirmed Match
Evidence Match
Evidence Found
Potential Match
Gap
```

This produces a more informative result than a simple percentage-based keyword match.

---

# 🔐 Privacy

The system processes the uploaded CV during the analysis workflow.

The project does not include a real candidate CV in the public repository.

Sample/demo documents can be used for testing without exposing personal candidate information.

---

# ⚠️ Limitations

CV2JOB-Agent is an analytical assistance system and should not be treated as an automated hiring decision system.

Important limitations include:

- Semantic similarity does not prove actual skill proficiency.
- A CV may contain skills that are not sufficiently demonstrated through evidence.
- Different wording can affect matching results.
- Job descriptions may be incomplete or inconsistently structured.
- The compatibility score is not a probability of getting hired.
- Recommendations should be validated against the candidate's actual experience.

---

# 🔮 Future Improvements

Potential future improvements include:

- Support for additional document formats
- More advanced skill ontology and skill aliases
- Better experience-to-requirement mapping
- Industry-specific requirement models
- Multiple job description comparison
- Job recommendation based on candidate profile
- Resume bullet optimization
- ATS-oriented resume feedback
- Learning-resource recommendations for identified gaps
- Job application tracking
- Historical progress tracking
- LLM-assisted explanation generation
- Improved semantic models
- Cloud-based persistent user profiles

---

# 🎓 Project Objective

The primary objective of CV2JOB-Agent is to bridge the gap between:

```text
What the Job Requires
        ↓
What the Candidate Demonstrates
        ↓
What Evidence Exists
        ↓
What Is Missing
        ↓
What Should Be Improved
```

The system therefore goes beyond simple keyword matching and provides a structured reasoning pipeline for CV-to-job alignment.

---

# 🧪 Engineering Approach

The project was developed as a modular pipeline rather than a single large script.

Each major responsibility is isolated into a separate component:

```text
Parser
   ↓
Analyzer
   ↓
Matcher
   ↓
Evidence Mapper
   ↓
Semantic Matcher
   ↓
Integrated Matcher
   ↓
Gap Analyzer
   ↓
Improvement Planner
   ↓
Report Generator
```

This makes the system easier to:

- Test
- Debug
- Extend
- Maintain
- Replace individual components
- Experiment with different matching strategies

The modular architecture also allows deterministic and semantic approaches to complement rather than replace each other.

---

# 🏆 Project Highlights

- Modular end-to-end architecture
- Multiple document format support
- Deterministic + semantic matching
- Evidence-aware analysis
- Requirement-level classification
- Gap prioritization
- Actionable improvement planning
- Interactive Streamlit interface
- Automated backend testing
- 142 verified backend tests passing

---

# 👩‍💻 Author

**Niharika**

B.Tech – Computer Science & Engineering  
Specialization: Data Science

---

## 📌 Disclaimer

CV2JOB-Agent is intended to assist candidates in understanding and improving their CV-to-job alignment.

It should not be used as the sole basis for employment or hiring decisions.
