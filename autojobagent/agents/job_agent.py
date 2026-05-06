"""Agent that turns raw job dictionaries into stored, scored database rows."""

import re
from hashlib import sha1
from pathlib import Path

from llm.cover_letter import generate_cover_letter
from llm.resume_matcher import explain_match_details, match_resume_to_job
from llm.skill_extractor import extract_skills
from db.database import session, Job


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class JobAgent:
    """
    Agent responsible for processing individual jobs: matching with resume,
    extracting skills, and storing in database if they meet the threshold.
    """

    def __init__(self, resume_text, threshold, cover_letter_dir=None, store_low_matches=True):
        self.resume_text = resume_text
        self.threshold = threshold
        self.cover_letter_dir = Path(cover_letter_dir or PROJECT_ROOT / "cover_letters")
        self.store_low_matches = store_low_matches

    def process_job(self, job_data):
        """
        Processes a single job: matches with resume, extracts skills,
        and stores if score >= threshold.

        Args:
            job_data (dict): Job details from scraper.

        Returns:
            bool: True if job was stored, False otherwise.
        """
        link = job_data.get("link")
        description = job_data.get("description", "")
        if not link or not description:
            return False

        existing = session.query(Job).filter_by(link=link).first()
        if existing:
            return False

        score, reason, language_required = match_resume_to_job(
            self.resume_text, description
        )
        match_category = "Good match" if score >= self.threshold else "Low match"
        detailed_reason = explain_match_details(
            self.resume_text,
            description,
            score,
            self.threshold,
        )

        if score < self.threshold and not self.store_low_matches:
            return False

        skills = extract_skills(description, use_model=False)
        cover_letter_path = self._write_cover_letter(job_data, description)

        new_job = Job(
            title=job_data.get("title", "Untitled role"),
            company=job_data.get("company", "Unknown company"),
            link=link,
            description=description,
            portal=job_data.get("portal", job_data.get("source", "Unknown")),
            search_query=job_data.get("search_query", ""),
            location=job_data.get("location", ""),
            score=score,
            reason=reason,
            low_match_reason=detailed_reason,
            match_category=match_category,
            skills=skills,
            cover_letter_path=str(cover_letter_path),
            language_required=language_required,
            salary=job_data.get("salary", ""),
        )

        try:
            session.add(new_job)
            session.commit()
            return score >= self.threshold
        except Exception:
            session.rollback()
            raise

    def _write_cover_letter(self, job_data, description):
        """Create one markdown cover-letter file per stored job."""
        self.cover_letter_dir.mkdir(parents=True, exist_ok=True)
        title = job_data.get("title", "job")
        company = job_data.get("company", "company")
        slug = _slugify(f"{company}-{title}")[:90]
        link_hash = sha1(job_data.get("link", slug).encode("utf-8")).hexdigest()[:8]
        output_path = self.cover_letter_dir / f"{slug}-{link_hash}.md"
        cover_letter = generate_cover_letter(
            self.resume_text,
            description,
            use_model=False,
        )
        output_path.write_text(cover_letter, encoding="utf-8")
        return output_path


def _slugify(value):
    """Convert a title/company string into a filesystem-friendly slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "cover-letter"
