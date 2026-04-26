from scrapers.indeed import scrape_indeed
from scrapers.xing import scrape_xing
from scrapers.linkedin import scrape_linkedin

def aggregate_jobs(locations, roles):
    """
    Aggregates job listings from all configured scrapers.

    Args:
        locations (list): List of location strings.
        roles (list): List of role strings.

    Returns:
        list: Combined list of job dictionaries from all sources.
    """
    jobs = []

    # Scrape from Indeed
    indeed_jobs = scrape_indeed(locations, roles)
    jobs.extend(indeed_jobs)

    # Scrape from Xing (placeholder)
    xing_jobs = scrape_xing(locations, roles)
    jobs.extend(xing_jobs)

    # Scrape from LinkedIn (safe/placeholder)
    linkedin_jobs = scrape_linkedin(locations, roles)
    jobs.extend(linkedin_jobs)

    # Remove duplicates based on link
    unique_jobs = []
    seen_links = set()
    for job in jobs:
        if job['link'] not in seen_links:
            unique_jobs.append(job)
            seen_links.add(job['link'])

    return unique_jobs