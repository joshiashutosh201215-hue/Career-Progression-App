"""LinkedIn ingestion placeholder.

LinkedIn has strict platform rules and anti-scraping controls, so this module
stays intentionally conservative until an approved API/manual import path is
available.
"""

def scrape_linkedin(locations, roles, max_results=20):
    """
    Safe LinkedIn job ingestion.
    Due to LinkedIn's policies, aggressive scraping is avoided.
    This is a placeholder for manual or API-based ingestion if available.
    Currently returns an empty list.

    Args:
        locations (list): List of locations.
        roles (list): List of roles.

    Returns:
        list: Empty list (placeholder).
    """
    _ = (locations, roles, max_results)
    return []
