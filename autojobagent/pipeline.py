import yaml
from scrapers.jobs_aggregator import aggregate_jobs
from agents.job_agent import JobAgent
from db.database import session

def run_pipeline():
    """
    Main pipeline to fetch jobs, process them, and store relevant ones.
    Loads config, aggregates jobs, and uses JobAgent to process each.
    """
    # Load configuration
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Load resume
    with open(config['resume_path'], 'r') as f:
        resume_text = f.read()

    # Aggregate jobs from all sources
    locations = config['locations']
    roles = config['roles']
    jobs = aggregate_jobs(locations, roles)

    # Initialize JobAgent
    threshold = config['min_match_score']
    agent = JobAgent(resume_text, threshold)

    # Process each job
    processed_count = 0
    for job in jobs:
        if agent.process_job(job):
            processed_count += 1

    print(f"Pipeline completed. Processed {processed_count} new relevant jobs.")

if __name__ == "__main__":
    run_pipeline()