# AutoJobAgent

AutoJobAgent is a local AI-assisted job matching app. It loads your resume, reads job posts, scores each job against your background, extracts important skills, and shows the results in a Streamlit dashboard.

## Verified Status

This version was run locally with the project virtualenv on April 26, 2026.

- `python run_pipeline.py --live --reset --limit 30 --offline-models` completed successfully.
- The live run connected to Arbeitnow, Bundesagentur, and Remotive, storing 27 jobs.
- The live run classified 9 jobs as good matches and 18 jobs as low matches.
- Indeed returned HTTP 403 from direct scraping, so the dashboard keeps it as a portal section plus manual link.
- LinkedIn and Xing are portal sections with manual/API handoff because direct authenticated scraping is not used.
- The Streamlit dashboard started successfully at `http://127.0.0.1:8501`.
- The original `KeyError: Unknown task text2text-generation` is fixed.

## Quick Start

```bash
cd /home/user/Career-Progression-App/autojobagent
python3 -m venv .career_app_venv
source .career_app_venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py --live --reset --limit 30 --offline-models
streamlit run ui/dashboard.py --server.port 8501
```

Open `http://127.0.0.1:8501` after Streamlit starts.

## Useful Commands

```bash
# Live portal search using configured public sources
python run_pipeline.py --live --reset --limit 30 --offline-models

# Focus live search to public/no-key sources
python run_pipeline.py --live --reset --portals arbeitnow,bundesagentur,remotive --offline-models

# Safe local demo using data/demo_jobs.json
python run_pipeline.py --demo --reset --offline-models

# Dashboard
streamlit run ui/dashboard.py --server.port 8501
```

## What Was Fixed

- Replaced the removed Hugging Face `text2text-generation` pipeline task with direct `AutoTokenizer` and `AutoModelForSeq2SeqLM` calls.
- Moved model loading out of import time so the app can start even if a model is missing.
- Added offline-safe fallbacks for matching, skill extraction, and cover-letter generation.
- Added live public-source connectors for Arbeitnow, Bundesagentur, and Remotive.
- Kept Indeed, LinkedIn, Xing, StepStone, Glassdoor, and EURES as dashboard sections/manual links when direct access is blocked or not appropriate.
- Added `data/demo_jobs.json` for quick offline smoke tests.
- Anchored SQLite to `autojobagent/jobs.db` so pipeline and dashboard read the same database.
- Removed the blocking Playwright/manual `input()` flow from the dashboard apply action.
- Added timeouts and safer error handling around live scraping.
- Added generated cover-letter markdown files under `cover_letters/`.
- Changed the match threshold to 40%; jobs below 40% are still stored as low matches with reasons.

## Module Map

| Module | Responsibility |
| --- | --- |
| `run_pipeline.py` | Small executable CLI wrapper. |
| `pipeline.py` | Loads config/resume, selects demo or live jobs, sends jobs to `JobAgent`, prints run summary. |
| `config/config.yaml` | Roles, locations, threshold, resume path, demo mode, model names. |
| `data/resume.txt` | Candidate resume used for matching. |
| `data/demo_jobs.json` | Local demo jobs for repeatable testing. |
| `scrapers/jobs_aggregator.py` | Calls each source scraper and deduplicates jobs by link. |
| `scrapers/indeed.py` | Basic live Indeed fetcher with timeout. |
| `scrapers/public_apis.py` | Public/no-key connectors for Arbeitnow, Bundesagentur, Remotive, plus manual portal links. |
| `scrapers/linkedin.py`, `scrapers/xing.py` | Safe placeholders until approved API/manual ingestion is added. |
| `agents/job_agent.py` | Scores one job, classifies it, extracts skills, writes a cover letter, and stores the row. |
| `agents/apply_agent.py` | Opens job links for manual application. It does not auto-submit forms. |
| `llm/model_utils.py` | Central Hugging Face model loading, text generation, German requirement detection, keyword fallback helpers. |
| `llm/resume_matcher.py` | Computes resume-job score with embeddings or fallback keyword overlap. |
| `llm/skill_extractor.py` | Extracts top skills with model output validation and deterministic fallback. |
| `llm/cover_letter.py` | Generates or templates a cover letter draft. |
| `db/database.py` | SQLAlchemy model and SQLite connection. |
| `ui/dashboard.py` | Streamlit UI for metrics, skills demand, jobs, and applied status. |

## Module Handshake

1. `run_pipeline.py` calls `pipeline.main()`.
2. `pipeline.py` reads `config/config.yaml`.
3. `pipeline.py` loads `data/resume.txt`.
4. `pipeline.py` loads either `data/demo_jobs.json` or live scraper results.
5. `JobAgent.process_job()` receives one job dictionary at a time.
6. `resume_matcher.py` asks `model_utils.py` for the embedding model and calculates a similarity score.
7. `skill_extractor.py` extracts visible skills for every stored job.
8. `cover_letter.py` creates a markdown cover-letter draft for the job.
9. `JobAgent` writes the job into SQLite through `db/database.py`.
10. `ui/dashboard.py` reads the same SQLite database and renders portal-wise tabs, job links, cover-letter downloads, and match reasons.

## AI Concepts In This App

- Embeddings: the resume and job description are converted into numeric vectors that represent meaning.
- Cosine similarity: the app compares those vectors to estimate how aligned the resume is with the job.
- Thresholding: jobs at or above `min_match_score` are "Good match"; jobs below it are "Low match" but still stored with reasons.
- Generation: `google/flan-t5-small` is used for short text tasks when it produces a valid answer.
- Validation: generated text is checked before use. If it looks weak, the app uses deterministic rules instead.
- Fallbacks: the app remains executable even when Hugging Face files are not cached or the network is unavailable.

## Hugging Face Model Choice

The default embedding model is `sentence-transformers/all-MiniLM-L6-v2`. It was chosen because it is small, fast on CPU, widely used for semantic similarity, and strong enough for resume-job matching without needing a GPU.

The default generation model is `google/flan-t5-small`. It was chosen because it is open source, CPU-friendly, and easy to run inside Python. In testing, it was not always reliable for polished cover letters, so the app validates its output and falls back to a clean template when needed.

## Why Not Ollama By Default

Ollama is a good option for larger local chat models, but it requires a separate local service, separate model pulls, and usually more RAM/disk than this small project needs. Hugging Face was a better default here because both embedding and generation can be called directly from Python and cached with the same dependency stack.

Ollama would be a reasonable future upgrade for higher-quality cover letters, while Hugging Face embeddings should still remain the better default for scoring.

## Demo

See `DEMO.md` for a repeatable terminal demo and expected output.

## Notes

- Live scraping can break when job boards change their HTML or block automated traffic.
- Indeed returned 403 during verification, which means it blocks this direct request path from the local environment.
- LinkedIn and Xing are intentionally manual/API sections to avoid unsafe authenticated scraping.
- The source files now include module docstrings and focused comments where they help explain the flow. The code is not commented line-by-line because that would make it harder to read and maintain.
