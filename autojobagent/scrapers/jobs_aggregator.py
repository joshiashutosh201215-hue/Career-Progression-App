"""Collect jobs from each configured source and remove duplicates."""

from scrapers.indeed import scrape_indeed
from scrapers.linkedin import scrape_linkedin
from scrapers.public_apis import (
    scrape_arbeitnow,
    scrape_bundesagentur,
    scrape_remotive,
)
from scrapers.xing import scrape_xing


def aggregate_jobs(locations, roles, enabled_portals=None, max_results_per_portal=20):
    """
    Aggregates job listings from all configured scrapers.

    Args:
        locations (list): List of location strings.
        roles (list): List of role strings.

    Returns:
        list: Combined list of job dictionaries from all sources.
    """
    jobs = []
    enabled = {portal.lower() for portal in enabled_portals or []}
    scraper_functions = [
        ("Indeed", scrape_indeed),
        ("Arbeitnow", scrape_arbeitnow),
        ("Bundesagentur", scrape_bundesagentur),
        ("Remotive", scrape_remotive),
        ("Xing", scrape_xing),
        ("LinkedIn", scrape_linkedin),
    ]

    for source_name, scraper in scraper_functions:
        if enabled and source_name.lower() not in enabled:
            continue
        try:
            source_jobs = scraper(
                locations,
                roles,
                max_results=max_results_per_portal,
            )
            jobs.extend(source_jobs)
            print(f"{source_name}: collected {len(source_jobs)} jobs.")
        except Exception as exc:
            print(f"{source_name}: skipped after error: {exc}")

    unique_jobs = []
    seen_links = set()
    for job in jobs:
        link = job.get("link")
        if link and link not in seen_links:
            unique_jobs.append(job)
            seen_links.add(link)

    return unique_jobs
