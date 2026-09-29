from typing import Any


def create_empty_cv_profile() -> dict[str, Any]:
    """
    Create the standard internal structure used by the CV analyzer.
    """

    return {
        "name": "",
        "contact": {
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
        },
        "summary": "",
        "education": [],
        "skills": {
            "programming": [],
            "data_analysis": [],
            "machine_learning": [],
            "databases": [],
            "visualization": [],
            "developer_tools": [],
            "cloud": [],
            "other": [],
        },
        "experience": [],
        "projects": [],
        "certifications": [],
        "activities": [],
        "languages": [],
        "raw_text": "",
    }


def create_empty_job_profile() -> dict[str, Any]:
    """
    Create the standard internal structure used by the
    Job Description Analyzer.
    """

    return {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "soft_skills": [],
        "responsibilities": [],
        "education_requirements": [],
        "experience_requirements": [],
        "location": "",
        "raw_text": "",
    }