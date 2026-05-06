# AutoJobAgent Demo

There are two demos:

- A live portal demo that connects to public/no-key sources.
- A local demo that uses `data/demo_jobs.json` when you want a quick offline smoke test.

## Live Portal Demo

```bash
cd /home/user/Career-Progression-App/autojobagent
source .career_app_venv/bin/activate
python run_pipeline.py --live --reset --limit 30 --offline-models
streamlit run ui/dashboard.py --server.port 8501
```

Open:

```text
http://127.0.0.1:8501
```

## Expected Terminal Output

```text
Indeed skipped 42 searches; last error: 403 Client Error: Forbidden ...
Indeed: collected 0 jobs.
Arbeitnow: collected 7 jobs.
Bundesagentur: collected 10 jobs.
Remotive: collected 10 jobs.
Xing: collected 0 jobs.
LinkedIn: collected 0 jobs.
Pipeline completed. Source=live; jobs seen=27; new good matches=9; database rows=27.
```

The dashboard should show portal tabs for Indeed, LinkedIn, Xing, Arbeitnow, Bundesagentur, Remotive, StepStone, Glassdoor, EURES, and Other.

The verified live run found 9 good matches. The strongest examples were:

```text
Bundesagentur | 56.99 | Functional Safety Engineer (m/f/d) | MOTOR Ai GmbH
Bundesagentur | 56.89 | Embedded Hardware Engineer (m/w/d) | Schmitt GmbH
Bundesagentur | 53.15 | Embedded Software Engineer (m/w/d) | CarByte
Bundesagentur | 53.07 | Software Architect w/m/d | Computacenter AG & Co. oHG
Arbeitnow     | 42.35 | Embedded Software Engineer (m/w/d) | NOVUS GmbH
```

## Offline Demo

```bash
python run_pipeline.py --demo --reset --offline-models
```

Expected output:

```text
Pipeline completed. Source=demo; jobs seen=3; new good matches=1; database rows=3.
```

## What The Demo Proves

- The pipeline entry point works.
- The SQLite database is created and shared with the dashboard.
- The app can connect to live public job sources.
- The embedding-based scorer can rank embedded/software roles against the resume.
- Jobs at or above 40% are marked good matches.
- Jobs below 40% are still stored with low-match reasons.
- Cover-letter markdown files are generated for stored jobs.
- The Streamlit dashboard can read and display portal-wise results.

## Why Some Portals Are Manual

- Indeed returned HTTP 403 from direct HTML scraping in the verified run.
- LinkedIn and Xing are not scraped because they commonly require authenticated sessions and have anti-scraping controls.
- StepStone, Glassdoor, and EURES are exposed as manual search links until a stable approved API/import path is added.

## Audio Or Video Demo

I could not record an audio/video demo from this terminal-only execution environment because there is no browser capture or audio device exposed here. The commands above are the reproducible demo. If you run them locally, the Streamlit UI at `http://127.0.0.1:8501` is the visual demo.
