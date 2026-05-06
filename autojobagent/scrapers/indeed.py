"""Basic Indeed scraper used only for explicit live runs."""

import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)


def scrape_indeed(locations, roles, max_results=20):
    """
    Scrapes job listings from Indeed based on provided locations and roles.
    Uses requests and BeautifulSoup for parsing.

    Args:
        locations (list): List of location strings (e.g., ['Germany', 'Austria']).
        roles (list): List of role strings (e.g., ['Software Engineer']).

    Returns:
        list: List of dictionaries with job details.
    """
    jobs = []
    error_count = 0
    last_error = ""
    base_url = "https://de.indeed.com/jobs"

    for location in locations:
        for role in roles:
            params = {
                "q": role,
                "l": location,
            }
            try:
                response = requests.get(
                    base_url,
                    params=params,
                    headers={"User-Agent": USER_AGENT},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                job_cards = soup.find_all("div", class_="job_seen_beacon")

                for card in job_cards[:10]:
                    title_elem = card.find("h2", class_="jobTitle")
                    title = title_elem.text.strip() if title_elem else "N/A"

                    company_elem = card.find("span", class_="companyName")
                    company = company_elem.text.strip() if company_elem else "N/A"

                    link_elem = card.find("a", href=True)
                    link = (
                        urljoin("https://de.indeed.com", link_elem["href"])
                        if link_elem
                        else ""
                    )

                    desc_elem = card.find("div", class_="job-snippet")
                    description = desc_elem.text.strip() if desc_elem else ""

                    salary_elem = card.find("div", class_="salary-snippet")
                    salary = salary_elem.text.strip() if salary_elem else ""

                    jobs.append(
                        {
                            "title": title,
                            "company": company,
                            "link": link,
                            "description": description,
                            "salary": salary,
                            "portal": "Indeed",
                            "search_query": role,
                            "location": location,
                        }
                    )
                    if len(jobs) >= max_results:
                        return jobs

                time.sleep(1)

            except Exception as e:
                error_count += 1
                last_error = str(e)
                continue

    if error_count:
        print(f"Indeed skipped {error_count} searches; last error: {last_error}")

    return jobs
