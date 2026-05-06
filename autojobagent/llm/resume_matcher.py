"""Resume-to-job matching logic.

The primary scorer uses sentence embeddings, which compare meaning rather than
exact words.  A keyword fallback is kept on purpose so the demo still works in
offline classrooms or first-run environments where models are not cached yet.
"""

from llm.model_utils import (
    LocalModelError,
    detect_mandatory_german,
    extract_keyword_skills,
    get_embedder,
    important_tokens,
)


def _format_reasoning(score, scoring_method):
    """Produce a short reasoning statement for the similarity score."""
    if score >= 85:
        fit = "strongly aligned in skills, experience, and role focus."
    elif score >= 65:
        fit = "a good fit, though some domain details are less closely matched."
    elif score >= 45:
        fit = "relevant, but the match is moderate and some expected skills are not clearly present."
    else:
        fit = "a lower match because only limited overlap was found."

    return f"The resume is {fit} Scoring method: {scoring_method}."


def match_resume_to_job(resume_text, job_description):
    """
    Matches a resume with a job description using sentence embeddings.
    Returns a score (0-100), reasoning, and whether German is mandatory.

    Args:
        resume_text (str): The full text of the candidate's resume.
        job_description (str): The job description text.

    Returns:
        tuple: (score (float), reasoning (str), language_required (str))
    """
    if not resume_text or not job_description:
        return 0.0, "Missing resume or job description.", ""

    try:
        score = _semantic_score(resume_text, job_description)
        scoring_method = "Hugging Face sentence embeddings"
    except LocalModelError:
        score = _keyword_score(resume_text, job_description)
        scoring_method = "keyword fallback because the embedding model was unavailable"

    score = max(0.0, min(100.0, score))
    reasoning = _format_reasoning(score, scoring_method)
    language_required = detect_mandatory_german(job_description)
    return score, reasoning, language_required


def explain_match_details(resume_text, job_description, score, threshold):
    """Explain which extracted skills are present or missing from the resume."""
    required_skills = extract_keyword_skills(job_description, max_items=8)
    present_skills = [
        skill for skill in required_skills if _skill_is_visible(skill, resume_text)
    ]
    missing_skills = [
        skill for skill in required_skills if skill not in present_skills
    ]

    if score >= threshold:
        if present_skills:
            return "Good match because these job skills appear in the resume: " + ", ".join(present_skills[:6]) + "."
        return "Good match because the embedding model found strong semantic alignment."

    if missing_skills:
        return (
            f"Low match because the score is below {threshold}% and these extracted "
            "requirements are not clearly visible in the resume: "
            + ", ".join(missing_skills[:6])
            + "."
        )
    return (
        f"Low match because the score is below {threshold}% even though some terms overlap; "
        "the role focus is semantically weaker than the strongest embedded-software matches."
    )


def _semantic_score(resume_text, job_description):
    """Calculate cosine similarity using the configured sentence embedder."""
    try:
        from sentence_transformers import util

        embedder = get_embedder()
        embeddings = embedder.encode(
            [resume_text, job_description],
            convert_to_tensor=True,
            show_progress_bar=False,
        )
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        return round(float(similarity) * 100.0, 2)
    except LocalModelError:
        raise
    except Exception as exc:
        raise LocalModelError(f"Semantic matching failed: {exc}") from exc


def _keyword_score(resume_text, job_description):
    """Score a job with transparent token and skill overlap rules."""
    resume_tokens = set(important_tokens(resume_text))
    job_tokens = set(important_tokens(job_description))
    if not job_tokens:
        return 0.0

    token_overlap = len(resume_tokens.intersection(job_tokens)) / len(job_tokens)
    required_skills = extract_keyword_skills(job_description, max_items=12)
    skill_hits = [
        skill
        for skill in required_skills
        if skill.lower() in resume_text.lower()
        or skill.lower().replace("/", "") in resume_text.lower()
    ]
    skill_overlap = len(skill_hits) / len(required_skills) if required_skills else 0.0
    blended_score = (token_overlap * 45.0) + (skill_overlap * 55.0)
    return round(blended_score, 2)


def _skill_is_visible(skill, resume_text):
    """Check whether a skill label or compact variant appears in the resume."""
    resume_lower = resume_text.lower()
    skill_lower = skill.lower()
    compact_skill = skill_lower.replace("/", "").replace("-", "").replace(" ", "")
    compact_resume = resume_lower.replace("/", "").replace("-", "").replace(" ", "")
    return skill_lower in resume_lower or compact_skill in compact_resume
