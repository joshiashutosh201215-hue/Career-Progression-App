from llm.resume_matcher import match_resume_to_job
from llm.skill_extractor import extract_skills
from db.database import session, Job

class JobAgent:
    """
    Agent responsible for processing individual jobs: matching with resume,
    extracting skills, and storing in database if they meet the threshold.
    """

    def __init__(self, resume_text, threshold):
        self.resume_text = resume_text
        self.threshold = threshold

    def process_job(self, job_data):
        """
        Processes a single job: matches with resume, extracts skills,
        and stores if score >= threshold.

        Args:
            job_data (dict): Job details from scraper.

        Returns:
            bool: True if job was stored, False otherwise.
        """
        # Check if job already exists
        existing = session.query(Job).filter_by(link=job_data['link']).first()
        if existing:
            return False

        # Match resume to job
        score, reason, language_required = match_resume_to_job(
            self.resume_text, job_data['description']
        )

        if score >= self.threshold:
            # Extract skills
            skills = extract_skills(job_data['description'])

            # Create new Job instance
            new_job = Job(
                title=job_data['title'],
                company=job_data['company'],
                link=job_data['link'],
                description=job_data['description'],
                score=score,
                reason=reason,
                skills=skills,
                language_required=language_required,
                salary=job_data.get('salary', '')
            )

            # Add to session
            session.add(new_job)
            session.commit()
            return True

        return False