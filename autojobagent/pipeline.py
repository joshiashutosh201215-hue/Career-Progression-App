"""Pipeline orchestration for fetching, scoring, and storing job posts."""

import argparse
import json
from pathlib import Path
from shutil import rmtree
from typing import Optional

import yaml
from scrapers.jobs_aggregator import aggregate_jobs
from agents.job_agent import JobAgent
from db.database import Job, session
from llm.model_utils import configure_models

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
DEFAULT_DEMO_JOBS_PATH = PROJECT_ROOT / "data" / "demo_jobs.json"


def run_pipeline(
    config_path=None,
    demo=None,
    limit=None,
    reset=False,
    offline_models=False,
    portals=None,
):
    """
    Main pipeline to fetch jobs, process them, and store relevant ones.
    Loads config, aggregates jobs, and uses JobAgent to process each.
    """
    config = load_config(config_path)
    if offline_models:
        config.setdefault("models", {})["local_files_only"] = True
    configure_models(config.get("models"))

    if reset:
        session.query(Job).delete()
        session.commit()
        clear_cover_letters(resolve_project_path(config.get("cover_letter_dir", "cover_letters")))

    resume_text = load_text_file(resolve_project_path(config['resume_path']))
    use_demo = bool(config.get("demo_mode", False)) if demo is None else demo
    enabled_portals = portals or config.get("live_portals", [])
    max_results_per_portal = config.get("max_results_per_portal", 20)
    jobs = (
        load_demo_jobs()
        if use_demo
        else aggregate_jobs(
            config["locations"],
            config["roles"],
            enabled_portals=enabled_portals,
            max_results_per_portal=max_results_per_portal,
        )
    )
    source = "demo" if use_demo else "live"

    if not jobs and not use_demo and config.get("fallback_to_demo", True):
        print("No live jobs were collected, so the pipeline is using demo jobs.")
        jobs = load_demo_jobs()
        source = "demo fallback"

    if limit is None:
        limit = config.get("max_jobs_per_run")
    if limit:
        jobs = jobs[:limit]

    agent = JobAgent(
        resume_text,
        config["min_match_score"],
        cover_letter_dir=resolve_project_path(config.get("cover_letter_dir", "cover_letters")),
        store_low_matches=config.get("store_low_matches", True),
    )
    processed_count = 0
    for job in jobs:
        if agent.process_job(job):
            processed_count += 1

    summary = {
        "source": source,
        "jobs_seen": len(jobs),
        "new_good_matches": processed_count,
        "database_rows": session.query(Job).count(),
    }
    print(
        "Pipeline completed. "
        f"Source={summary['source']}; "
        f"jobs seen={summary['jobs_seen']}; "
        f"new good matches={summary['new_good_matches']}; "
        f"database rows={summary['database_rows']}."
    )
    return summary


def load_config(config_path=None):
    """Read YAML configuration from the project config folder by default."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with path.open('r', encoding='utf-8') as file_obj:
        return yaml.safe_load(file_obj)


def resolve_project_path(path_value):
    """Resolve relative paths from the autojobagent project directory."""
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_text_file(path):
    """Load UTF-8 text from disk."""
    with Path(path).open('r', encoding='utf-8') as file_obj:
        return file_obj.read()


def load_demo_jobs(path=None):
    """Load stable local jobs used for smoke tests and demos."""
    demo_path = Path(path) if path else DEFAULT_DEMO_JOBS_PATH
    with demo_path.open('r', encoding='utf-8') as file_obj:
        return json.load(file_obj)


def clear_cover_letters(path):
    """Remove generated cover letters when the stored job database is reset."""
    cover_letter_dir = Path(path)
    if cover_letter_dir.exists() and cover_letter_dir.is_dir():
        rmtree(cover_letter_dir)


def main(argv: Optional[list] = None):
    """CLI entry point for demo and live runs."""
    parser = argparse.ArgumentParser(description="Run the AutoJobAgent pipeline.")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--demo", action="store_true", help="Use local demo jobs.")
    source_group.add_argument("--live", action="store_true", help="Scrape configured live sources.")
    parser.add_argument("--config", help="Path to a config YAML file.")
    parser.add_argument("--limit", type=int, help="Limit the number of jobs processed.")
    parser.add_argument(
        "--portals",
        help="Comma-separated live portals, e.g. arbeitnow,bundesagentur,remotive,indeed.",
    )
    parser.add_argument("--reset", action="store_true", help="Clear stored jobs before running.")
    parser.add_argument(
        "--offline-models",
        action="store_true",
        help="Use only cached Hugging Face files and fall back quickly if absent.",
    )
    args = parser.parse_args(argv)

    demo = True if args.demo else False if args.live else None
    portals = [portal.strip() for portal in args.portals.split(",")] if args.portals else None
    run_pipeline(
        config_path=args.config,
        demo=demo,
        limit=args.limit,
        reset=args.reset,
        offline_models=args.offline_models,
        portals=portals,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
