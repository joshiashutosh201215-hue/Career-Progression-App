"""Skill extraction for job descriptions.

The preferred path asks the local Hugging Face instruction model to summarize
the job requirements.  If that model is not downloaded yet, the deterministic
keyword fallback keeps the pipeline executable and transparent.
"""

import re

from llm.model_utils import LocalModelError, extract_keyword_skills, generate_text


def extract_skills(job_description, use_model=False):
    """
    Extract the top five required skills from a job description.

    Args:
        job_description (str): The job description text.

    Returns:
        str: Comma-separated string of top 5 skills.
    """
    if not job_description:
        return ""

    if use_model:
        prompt = (
            "Extract exactly five required job skills. "
            "Return only comma-separated skill names, no sentence, no explanation.\n\n"
            f"Job Description:\n{job_description}\n"
        )
        try:
            generated = generate_text(prompt, max_new_tokens=80)
            parsed_skills = _parse_skill_list(generated)
            if len(parsed_skills) >= 3:
                return ", ".join(parsed_skills[:5])
        except LocalModelError:
            pass

    return ", ".join(extract_keyword_skills(job_description, max_items=5))


def _parse_skill_list(generated_text):
    """Turn a model response into a clean list of short skill labels."""
    cleaned = generated_text.replace("\n", ",")
    cleaned = re.sub(r"\b(and|skills?:)\b", ",", cleaned, flags=re.IGNORECASE)
    skills = []

    for part in re.split(r"[,;|]", cleaned):
        candidate = re.sub(r"^\s*[-*\d.)]+\s*", "", part).strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if 2 <= len(candidate) <= 45 and "job description" not in candidate.lower():
            skills.append(candidate)

    unique_skills = []
    seen = set()
    for skill in skills:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            unique_skills.append(skill)

    return unique_skills
