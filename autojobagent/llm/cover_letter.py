"""Cover-letter generation helpers.

This module uses the same local Hugging Face generation model as the skill
extractor.  When the model is unavailable, it returns a plain deterministic
draft rather than failing the pipeline.
"""

from llm.model_utils import LocalModelError, extract_keyword_skills, generate_text


def generate_cover_letter(resume_text, job_description, use_model=False):
    """
    Generates a personalized cover letter based on the resume and job description.

    Args:
        resume_text (str): The candidate's resume.
        job_description (str): The job description.

    Returns:
        str: The generated cover letter.
    """
    if not resume_text or not job_description:
        return "Resume or job description missing."

    if use_model:
        prompt = (
            "Write a concise professional cover letter for this candidate and job. "
            "Use a polite tone, mention the strongest matching skills, and keep it under 180 words.\n\n"
            f"Resume:\n{resume_text}\n\n"
            f"Job Description:\n{job_description}\n\n"
            "Cover Letter:\n"
        )
        try:
            response = generate_text(prompt, max_new_tokens=220)
            if _looks_like_cover_letter(response):
                return response
        except LocalModelError:
            pass

    return _fallback_cover_letter(resume_text, job_description)


def _looks_like_cover_letter(text):
    """Reject model output that is only a summary or an unfinished fragment."""
    words = text.split()
    lower_text = text.lower()
    has_greeting = lower_text.startswith("dear") or "hiring team" in lower_text[:80]
    has_letter_shape = 40 <= len(words) <= 230 and "•" not in text
    return has_greeting and has_letter_shape


def _fallback_cover_letter(resume_text, job_description):
    """Create a readable template when local generation is unavailable."""
    skills = ", ".join(
        extract_keyword_skills(resume_text + "\n" + job_description, max_items=5)
    )
    return (
        "Dear Hiring Team,\n\n"
        "I am excited to apply for this role because it aligns closely with my background in "
        f"{skills}. My experience includes delivering embedded and system architecture work, "
        "coordinating cross-functional teams, and translating complex technical requirements "
        "into reliable production solutions.\n\n"
        "I would welcome the opportunity to discuss how my experience can support your team.\n\n"
        "Kind regards,\n"
        "Aashutosh Joshi"
    )
