"""Public/no-key job sources that can be called from the live pipeline."""

from html import unescape
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT_SECONDS = 20
USER_AGENT = "AutoJobAgent/1.0 (+local job matching demo)"


def scrape_arbeitnow(locations, roles, max_results=30):
    """Fetch Europe-focused jobs from the public Arbeitnow API."""
    response = requests.get(
        "https://www.arbeitnow.com/api/job-board-api",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    raw_jobs = payload.get("data", payload if isinstance(payload, list) else [])
    normalized_jobs = []

    for item in raw_jobs:
        text_blob = " ".join(
            [
                item.get("title", ""),
                item.get("company_name", ""),
                item.get("location", ""),
                " ".join(item.get("tags") or []),
                _plain_text(item.get("description", "")),
            ]
        )
        if not _matches_search(text_blob, roles, locations):
            continue

        normalized_jobs.append(
            {
                "title": item.get("title", "Untitled role"),
                "company": item.get("company_name", "Unknown company"),
                "link": item.get("url", ""),
                "description": _plain_text(item.get("description", text_blob)),
                "salary": "",
                "portal": "Arbeitnow",
                "search_query": ", ".join(roles),
                "location": item.get("location", ""),
            }
        )
        if len(normalized_jobs) >= max_results:
            break

    return normalized_jobs


def scrape_remotive(locations, roles, max_results=30):
    """Fetch remote software jobs from Remotive's public API."""
    jobs = []
    for role in roles:
        response = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": role},
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("jobs", []):
            text_blob = " ".join(
                [
                    item.get("title", ""),
                    item.get("company_name", ""),
                    item.get("candidate_required_location", ""),
                    item.get("description", ""),
                    " ".join(item.get("tags") or []),
                ]
            )
            if not _matches_search(text_blob, roles, locations, allow_remote=True):
                continue

            jobs.append(
                {
                    "title": item.get("title", "Untitled role"),
                    "company": item.get("company_name", "Unknown company"),
                    "link": item.get("url", ""),
                    "description": _plain_text(item.get("description", text_blob)),
                    "salary": item.get("salary", ""),
                    "portal": "Remotive",
                    "search_query": role,
                    "location": item.get("candidate_required_location", "Remote"),
                }
            )
            if len(jobs) >= max_results:
                return jobs

    return jobs


def scrape_bundesagentur(locations, roles, max_results=30):
    """Fetch German jobs from the Bundesagentur job-search endpoint."""
    jobs = []
    for role in roles:
        for location in locations:
            response = requests.get(
                "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs",
                params={
                    "was": role,
                    "wo": location,
                    "angebotsart": "1",
                    "page": 1,
                    "size": 10,
                    "pav": "false",
                },
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                    "X-API-Key": "jobboerse-jobsuche",
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("stellenangebote", []):
                ref = item.get("refnr", "")
                title = item.get("titel") or item.get("beruf") or "Untitled role"
                company = item.get("arbeitgeber", "Unknown company")
                place = _extract_bundesagentur_location(item)
                description = _describe_bundesagentur_job(item, role, location)
                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "link": _bundesagentur_link(ref),
                        "description": description,
                        "salary": item.get("gehalt", ""),
                        "portal": "Bundesagentur",
                        "search_query": role,
                        "location": place or location,
                    }
                )
                if len(jobs) >= max_results:
                    return jobs

    return jobs


def manual_portal_searches(locations, roles):
    """Return manual search links for portals that should not be scraped blindly."""
    primary_role = quote_plus(roles[0] if roles else "embedded software")
    primary_location = quote_plus(locations[0] if locations else "Germany")
    return [
        {
            "portal": "LinkedIn",
            "url": f"https://www.linkedin.com/jobs/search/?keywords={primary_role}&location={primary_location}",
            "status": "Manual/API required; normal LinkedIn scraping is not used.",
        },
        {
            "portal": "Xing",
            "url": f"https://www.xing.com/jobs/search?keywords={primary_role}&location={primary_location}",
            "status": "Manual/API required; Xing commonly requires authenticated access.",
        },
        {
            "portal": "StepStone",
            "url": f"https://www.stepstone.de/jobs/{primary_role}/in-{primary_location}",
            "status": "Manual review link; HTML scraping may be blocked or unstable.",
        },
        {
            "portal": "Glassdoor",
            "url": f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={primary_role}",
            "status": "Manual review link; scraping often requires consent/session flows.",
        },
        {
            "portal": "EURES",
            "url": f"https://eures.europa.eu/job-search_en?keywords={primary_role}",
            "status": "Manual review link for European roles.",
        },
    ]


def _matches_search(text_blob, roles, locations, allow_remote=False):
    """Keep jobs that match at least a role or embedded-domain term."""
    lower_blob = text_blob.lower()
    role_hit = any(role.lower() in lower_blob for role in roles)
    domain_terms = [
        "embedded",
        "autosar",
        "software architect",
        "system engineer",
        "diagnostics",
        "uds",
        "doip",
        "ecu",
        "firmware",
        "automotive",
    ]
    domain_hit = any(term in lower_blob for term in domain_terms)
    location_hit = allow_remote or any(location.lower() in lower_blob for location in locations)
    return (role_hit or domain_hit) and location_hit


def _plain_text(html_or_text):
    """Convert HTML descriptions into compact text for matching and display."""
    if not html_or_text:
        return ""
    soup = BeautifulSoup(unescape(str(html_or_text)), "html.parser")
    return " ".join(soup.get_text(" ").split())


def _extract_bundesagentur_location(item):
    """Extract a readable location from a Bundesagentur search result."""
    arbeitsort = item.get("arbeitsort") or {}
    if isinstance(arbeitsort, dict):
        return ", ".join(
            part
            for part in [
                arbeitsort.get("ort"),
                arbeitsort.get("region"),
                arbeitsort.get("land"),
            ]
            if part
        )
    return str(arbeitsort or "")


def _describe_bundesagentur_job(item, role, requested_location):
    """Build a useful description from Bundesagentur summary fields."""
    values = [
        item.get("titel"),
        item.get("beruf"),
        item.get("arbeitgeber"),
        _extract_bundesagentur_location(item) or requested_location,
        item.get("arbeitszeitmodell"),
        item.get("befristung"),
        item.get("eintrittsdatum"),
        role,
    ]
    return ". ".join(str(value) for value in values if value)


def _bundesagentur_link(ref):
    """Build a browser link for a Bundesagentur job reference."""
    if not ref:
        return "https://www.arbeitsagentur.de/jobsuche/"
    return f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{quote_plus(ref)}"
