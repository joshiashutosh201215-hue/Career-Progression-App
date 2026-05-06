"""Streamlit dashboard for portal-wise job review and manual application."""

import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from agents.apply_agent import apply_to_job
from db.database import Job, session
from pipeline import load_config
from scrapers.public_apis import manual_portal_searches

GOOD_MATCH_THRESHOLD = 40
PORTAL_ORDER = [
    "Indeed",
    "LinkedIn",
    "Xing",
    "Arbeitnow",
    "Bundesagentur",
    "Remotive",
    "StepStone",
    "Glassdoor",
    "EURES",
    "Other",
]


def ordered_portals(job_rows):
    """Return configured portal tabs plus any unexpected portal names."""
    found = {portal_name(job) for job in job_rows}
    ordered = list(PORTAL_ORDER)
    extras = sorted(found.difference(set(ordered)))
    return ordered + extras


def portal_name(job):
    """Normalize an empty portal name for grouping."""
    return job.portal or "Other"


def split_skills(skills):
    """Split a comma-separated skill string into clean labels."""
    if not skills:
        return []
    return [skill.strip() for skill in skills.split(",") if skill.strip()]


def category_matches(job, selected_category, threshold):
    """Apply the match-type filter."""
    if selected_category == "All":
        return True
    category = job.match_category or (
        "Good match" if (job.score or 0) >= threshold else "Low match"
    )
    return category == selected_category


def empty_portal_message(portal):
    """Explain why a portal tab may currently have no stored jobs."""
    manual_only = {"LinkedIn", "Xing", "StepStone", "Glassdoor", "EURES"}
    if portal in manual_only:
        return (
            f"No stored {portal} jobs yet. Use the manual search links above, "
            "or add an approved API/manual import path."
        )
    return f"No stored {portal} jobs match the current filters. Run the live pipeline or lower the score filter."


def read_cover_letter(path_value):
    """Read a generated cover letter from disk if it exists."""
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def render_job(job, threshold):
    """Render one job card with apply and cover-letter actions."""
    score = job.score or 0
    category = job.match_category or ("Good match" if score >= threshold else "Low match")
    title = f"{job.title} at {job.company} ({score:.2f}%, {category})"

    with st.expander(title):
        cols = st.columns([2, 1, 1, 1])
        cols[0].write(f"**Portal:** {portal_name(job)}")
        cols[1].write(f"**Location:** {job.location or 'Not specified'}")
        cols[2].write(f"**Search:** {job.search_query or 'Not specified'}")
        cols[3].write(f"**Applied:** {'Yes' if job.applied else 'No'}")

        st.write(f"**Reasoning:** {job.reason}")
        st.write(f"**Match Detail:** {job.low_match_reason or 'No detailed reason stored.'}")
        st.write(f"**Skills:** {job.skills or 'Not available'}")
        st.write(f"**Language Required:** {job.language_required or 'None'}")
        st.write(f"**Salary:** {job.salary or 'Not specified'}")

        action_cols = st.columns([1, 1, 1, 5])
        action_cols[0].link_button("Job Link", job.link)

        cover_letter_text = read_cover_letter(job.cover_letter_path)
        if cover_letter_text:
            action_cols[1].download_button(
                "Cover Letter",
                cover_letter_text,
                file_name=Path(job.cover_letter_path).name,
                mime="text/markdown",
                key=f"cover_{job.id}",
            )
        else:
            action_cols[1].write("No cover letter")

        if not job.applied:
            if action_cols[2].button("Applied", key=f"apply_{job.id}"):
                job.applied = True
                session.commit()
                st.rerun()

        if action_cols[3].button("Open in Browser", key=f"open_{job.id}"):
            opened = apply_to_job(job.link)
            if opened:
                st.success("Job page open request sent. Apply manually, then mark it applied.")
            else:
                st.warning("Could not open a browser here. Use the Job Link button.")


st.set_page_config(page_title="AutoJobAgent", layout="wide")
st.title("AutoJobAgent Dashboard")

config = load_config()
jobs = session.query(Job).order_by(Job.score.desc()).all()
threshold = config.get("min_match_score", GOOD_MATCH_THRESHOLD)
manual_links = manual_portal_searches(config.get("locations", []), config.get("roles", []))

good_jobs = [job for job in jobs if (job.score or 0) >= threshold]
low_jobs = [job for job in jobs if (job.score or 0) < threshold]
applied_jobs = [job for job in jobs if job.applied]
portals_with_jobs = {portal_name(job) for job in jobs}

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Stored Jobs", len(jobs))
col2.metric("Good Matches", len(good_jobs))
col3.metric("Low Matches", len(low_jobs))
col4.metric("Applied", len(applied_jobs))
col5.metric("Portals", len(portals_with_jobs))

st.caption(
    f"Good match means score >= {threshold}%. Below {threshold}% is shown as low match with reasons."
)

with st.expander("Manual Portal Search Links", expanded=False):
    for item in manual_links:
        cols = st.columns([1, 2, 4])
        cols[0].write(f"**{item['portal']}**")
        cols[1].link_button("Open Search", item["url"])
        cols[2].write(item["status"])

st.subheader("Portal Overview")
overview_rows = []
for portal in ordered_portals(jobs):
    portal_jobs = [job for job in jobs if portal_name(job) == portal]
    overview_rows.append(
        {
            "Portal": portal,
            "Jobs": len(portal_jobs),
            "Good": len([job for job in portal_jobs if (job.score or 0) >= threshold]),
            "Low": len([job for job in portal_jobs if (job.score or 0) < threshold]),
            "Best Score": max([job.score or 0 for job in portal_jobs], default=0),
        }
    )
st.table(overview_rows)

st.subheader("Top Skills Demand")
skill_counts = Counter()
for job in jobs:
    for skill in split_skills(job.skills):
        skill_counts[skill] += 1

if skill_counts:
    st.bar_chart(dict(skill_counts.most_common(10)))
else:
    st.write("No skills data available yet.")

st.subheader("Portal-Wise Results")
minimum_score = st.slider("Minimum score", min_value=0, max_value=100, value=0, step=5)
category_filter = st.radio(
    "Match type",
    ["All", "Good match", "Low match"],
    horizontal=True,
)

portal_tabs = ordered_portals(jobs)
tabs = st.tabs(portal_tabs)
for tab, portal in zip(tabs, portal_tabs):
    with tab:
        portal_jobs = [
            job
            for job in jobs
            if portal_name(job) == portal
            and (job.score or 0) >= minimum_score
            and category_matches(job, category_filter, threshold)
        ]
        if not portal_jobs:
            st.info(empty_portal_message(portal))
            continue

        for job in portal_jobs:
            render_job(job, threshold)
