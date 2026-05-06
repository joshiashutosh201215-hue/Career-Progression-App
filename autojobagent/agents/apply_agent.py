"""Helpers for opening application links without automating form submission."""

import webbrowser


def apply_to_job(job_link):
    """
    Open a job page for manual application.

    The app deliberately avoids auto-submitting applications.  That keeps the
    workflow ethical, reviewable, and less likely to violate job-board terms.

    Args:
        job_link (str): The URL of the job posting.

    Returns:
        bool: True if the browser accepted the open request, otherwise False.
    """
    if not job_link:
        return False

    return webbrowser.open_new_tab(job_link)
