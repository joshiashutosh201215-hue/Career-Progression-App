# AutoJobAgent

An AI-powered job search system that fetches jobs from multiple platforms, semantically matches them with your resume, and provides a dashboard for management.

## Architecture

The system is modularly designed with the following components:

- **Scrapers**: Fetch job listings from platforms like Indeed, Xing, and LinkedIn (safe ingestion).
- **LLM Modules**: Use OpenAI API for resume-job matching, skill extraction, and cover letter generation.
- **Database**: SQLite with SQLAlchemy for storing job data.
- **Agents**: JobAgent processes jobs, ApplyAgent handles semi-assisted applications.
- **Pipeline**: Orchestrates the entire job fetching, processing, and storage workflow.
- **UI**: Streamlit dashboard for viewing and managing jobs.

Modules interact as follows:
1. Pipeline loads config and resume.
2. Aggregator collects jobs from scrapers.
3. JobAgent matches each job with resume using LLM, extracts skills, and stores if above threshold.
4. Dashboard queries database to display metrics, skills demand, and job list with apply options.

## Component Handshake

- Config (YAML) → Pipeline → Aggregator → Scrapers
- Pipeline → JobAgent → LLM (Matcher & Extractor) → Database
- Dashboard → Database → ApplyAgent (for opening job pages)

## Setup Instructions

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment: Create `.env` file with `OPENAI_API_KEY=your_key`
4. Update `config/config.yaml` with your roles, locations, and resume path.
5. Place your resume in `data/resume.txt`.
6. Run pipeline: `python run_pipeline.py`
7. Run dashboard: `streamlit run ui/dashboard.py`

## Run Instructions

### Local
- Pipeline: `python run_pipeline.py`
- Dashboard: `streamlit run ui/dashboard.py`

### GitHub Actions
- Automatically runs every 12 hours.
- Manual trigger via GitHub UI.
- Requires `OPENAI_API_KEY` in repository secrets.

## Limitations

- Indeed scraper uses basic parsing; may break if site changes.
- Xing and LinkedIn are placeholders due to scraping restrictions.
- LinkedIn ingestion is safe/manual only, no aggressive automation.
- OpenAI API costs apply for matching and extraction.

## Future Improvements

- Enhance scrapers with better error handling and rotation.
- Implement full LinkedIn API integration if accessible.
- Add more platforms (e.g., Glassdoor).
- Improve UI with filters and search.
- Add email notifications for new jobs.
- Implement user authentication for multi-user support.