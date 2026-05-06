"""Xing ingestion placeholder.

Xing usually requires authenticated access.  Returning an empty list keeps live
runs predictable while leaving a clear place for a compliant API/manual import.
"""

def scrape_xing(locations, roles, max_results=20):
    """
    Placeholder for Xing scraper.
    Xing scraping is complex due to login requirements and anti-scraping measures.
    This function returns an empty list for now.

    Args:
        locations (list): List of locations.
        roles (list): List of roles.

    Returns:
        list: Empty list (placeholder).
    """
    _ = (locations, roles, max_results)
    return []
