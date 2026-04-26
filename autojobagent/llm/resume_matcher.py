import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def match_resume_to_job(resume_text, job_description):
    """
    Uses OpenAI's GPT model to semantically match a resume with a job description.
    Returns a score (0-100), reasoning, and whether German language is mandatory.

    Args:
        resume_text (str): The full text of the candidate's resume.
        job_description (str): The job description to match against.

    Returns:
        tuple: (score (float), reasoning (str), language_required (str))
    """
    prompt = f"""
    Compare the following resume with the job description semantically (not just keywords).

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Provide a match score from 0 to 100, where 100 is a perfect semantic match based on skills, experience, and requirements.
    Also, provide a brief reasoning for the score.
    Additionally, check if the job description explicitly mentions German language as mandatory. If yes, set language_required to "German", otherwise empty string.

    Output in JSON format: {{"score": number, "reasoning": "text", "language_required": "German" or ""}}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )
        result = response.choices[0].message.content.strip()
        # Parse the JSON response
        data = json.loads(result)
        score = float(data.get('score', 0))
        reasoning = data.get('reasoning', 'No reasoning provided')
        language_required = data.get('language_required', '')
        return score, reasoning, language_required
    except Exception as e:
        # Fallback in case of error
        return 0.0, f"Error in matching: {str(e)}", ""