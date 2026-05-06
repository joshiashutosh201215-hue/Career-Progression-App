# AutoJobAgent Architecture

This document explains the app as a set of handshakes. A handshake means one module gives another module a clear piece of data and expects a clear result back.

## High-Level Flow

```text
config + resume
    -> pipeline
    -> job source
    -> JobAgent
    -> resume matcher
    -> skill extractor
    -> cover-letter writer
    -> database
    -> dashboard
```

## Handshake Details

| Step | Caller | Receiver | Data Sent | Data Returned |
| --- | --- | --- | --- | --- |
| 1 | `run_pipeline.py` | `pipeline.py` | CLI flags such as `--demo` or `--live` | Exit code and printed summary |
| 2 | `pipeline.py` | `config/config.yaml` | File read request | Roles, locations, threshold, model config |
| 3 | `pipeline.py` | `data/resume.txt` | File read request | Resume text |
| 4 | `pipeline.py` | `data/demo_jobs.json` or `scrapers/jobs_aggregator.py` | Demo/live source choice | List of job dictionaries |
| 5 | `pipeline.py` | `JobAgent` | Resume text and score threshold | Agent object |
| 6 | `JobAgent` | `resume_matcher.py` | Resume text and job description | Score, reason, language requirement |
| 7 | `resume_matcher.py` | `model_utils.py` | Text that needs embedding | Hugging Face embedder or fallback error |
| 8 | `JobAgent` | `skill_extractor.py` | Job description | Comma-separated skills |
| 9 | `JobAgent` | `cover_letter.py` | Resume and job description | Markdown cover-letter text |
| 10 | `JobAgent` | `db/database.py` | Job fields, portal, score, reason, cover-letter path | Stored SQLite row |
| 11 | `ui/dashboard.py` | `db/database.py` | Query request | Portal-wise jobs, metrics, reasons, links |

## Portal Sources

| Portal | Current Mode | Reason |
| --- | --- | --- |
| Arbeitnow | Live public API | No API key required, Europe/remote focused. |
| Bundesagentur | Live search endpoint | Useful for German roles and embedded/software searches. |
| Remotive | Live public API | Useful for remote software roles. |
| Indeed | Attempted HTML request plus dashboard section | Verified run returned HTTP 403, so manual link remains important. |
| LinkedIn | Manual/API section | Direct authenticated scraping is not used. |
| Xing | Manual/API section | Authenticated access and anti-scraping controls make blind scraping unsafe. |
| StepStone, Glassdoor, EURES | Manual search links | Added as relevant portals until stable approved connectors are added. |

## AI Scoring

The best path uses `sentence-transformers/all-MiniLM-L6-v2`.

1. The resume becomes an embedding vector.
2. The job description becomes another embedding vector.
3. Cosine similarity compares the angle between vectors.
4. The result is converted to a 0-100 score.
5. The configured threshold decides whether the job is a good match or low match.

If the embedding model is unavailable, `resume_matcher.py` uses a transparent keyword-overlap fallback. That is less intelligent than embeddings, but it keeps the program useful and explainable.

Jobs below the threshold are still stored. This is intentional: the dashboard can then explain why a job was weak instead of silently hiding it.

## AI Generation

The generation path uses `google/flan-t5-small` through direct Hugging Face `AutoTokenizer` and `AutoModelForSeq2SeqLM` calls.

The older `pipeline("text2text-generation")` call failed because the installed `transformers` version no longer registers that task. Direct model calls are more stable here because the app controls tokenization, generation, decoding, and validation.

Generated text is treated as a draft, not truth. For live runs, cover letters use the deterministic template by default so 30-job searches do not spend minutes generating weak FLAN-T5-small output. The model path remains available for experiments.

## Database Boundary

`db/database.py` owns SQLite setup. All modules import the same `session` object, so the pipeline and dashboard use the same `autojobagent/jobs.db` file.

The stored row includes:

- portal name
- source search query and location
- job link
- score
- good/low match category
- reason and low-match detail
- extracted skills
- generated cover-letter path
- applied flag

The dashboard does not call AI models. It only reads stored results. That keeps the UI fast and prevents model downloads from happening when someone opens the page.
