import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_skills(job_description):
    """
    Uses OpenAI's GPT model to extract the top 5 required skills from a job description.

    Args:
        job_description (str): The job description text.

    Returns:
        str: Comma-separated string of top 5 skills.
    """
    prompt = f"""
    Extract the top 5 most important required skills from the following job description.
    Focus on technical skills, soft skills, and domain-specific knowledge.
    Return only a comma-separated list of skills, no additional text.

    Job Description:
    {job_description}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        skills = response.choices[0].message.content.strip()
        # Clean up any extra text, assuming it's comma-separated
        return skills
    except Exception as e:
        return f"Error extracting skills: {str(e)}"