import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_cover_letter(resume_text, job_description):
    """
    Generates a personalized cover letter based on resume and job description.

    Args:
        resume_text (str): The candidate's resume.
        job_description (str): The job description.

    Returns:
        str: The generated cover letter.
    """
    prompt = f"""
    Generate a professional cover letter based on the following resume and job description.
    Tailor it to highlight relevant experience and skills.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Cover Letter:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        cover_letter = response.choices[0].message.content.strip()
        return cover_letter
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"