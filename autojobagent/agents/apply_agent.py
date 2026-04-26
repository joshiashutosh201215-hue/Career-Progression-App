from playwright.sync_api import sync_playwright

def apply_to_job(job_link):
    """
    Semi-assisted job application using Playwright.
    Opens the job page in a browser for manual application.
    Does NOT auto-submit or fill forms.

    Args:
        job_link (str): The URL of the job posting.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Headless=False to show browser
        page = browser.new_page()
        page.goto(job_link)
        # Wait for user to manually apply
        input("Press Enter after you have applied manually...")
        browser.close()