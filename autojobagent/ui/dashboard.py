import streamlit as st
from db.database import session, Job
from agents.apply_agent import apply_to_job
from collections import Counter

st.title("AutoJobAgent Dashboard")

# Metrics
total_jobs = session.query(Job).count()
relevant_jobs = session.query(Job).filter(Job.score >= 50).count()  # Using 50 as default threshold
applied_jobs = session.query(Job).filter(Job.applied == True).count()
low_match_jobs = session.query(Job).filter(Job.score <= 50).count()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", total_jobs)
col2.metric("Relevant Jobs", relevant_jobs)
col3.metric("Applied Jobs", applied_jobs)
col4.metric("Low Match Jobs", low_match_jobs)

# Skills Demand
st.subheader("Top 10 Skills Demand")
all_skills = []
for job in session.query(Job).all():
    if job.skills:
        all_skills.extend([skill.strip() for skill in job.skills.split(',')])

skill_counts = Counter(all_skills)
top_skills = skill_counts.most_common(10)
if top_skills:
    st.bar_chart({skill: count for skill, count in top_skills})
else:
    st.write("No skills data available yet.")

# Job List
st.subheader("Job Listings")
jobs = session.query(Job).order_by(Job.score.desc()).all()

for job in jobs:
    with st.expander(f"{job.title} at {job.company} (Score: {job.score})"):
        st.write(f"**Company:** {job.company}")
        st.write(f"**Score:** {job.score}")
        st.write(f"**Reasoning:** {job.reason}")
        st.write(f"**Skills:** {job.skills}")
        st.write(f"**Language Required:** {job.language_required if job.language_required else 'None'}")
        st.write(f"**Salary:** {job.salary if job.salary else 'Not specified'}")
        st.write(f"**Applied:** {'Yes' if job.applied else 'No'}")
        st.markdown(f"[View Job]({job.link})")

        if not job.applied:
            if st.button(f"Mark as Applied {job.id}", key=f"apply_{job.id}"):
                job.applied = True
                session.commit()
                st.success("Marked as applied!")
                st.rerun()

            if st.button(f"Apply Now {job.id}", key=f"open_{job.id}"):
                st.info("Opening job page for manual application...")
                apply_to_job(job.link)
                st.success("Job page opened. Apply manually and then mark as applied.")