"""Database setup and SQLAlchemy models for stored job matches."""

import os
from pathlib import Path

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'jobs.db'}"
DATABASE_URL = os.getenv("AUTOJOB_DATABASE_URL", DEFAULT_DATABASE_URL)


class Job(Base):
    """A job post that has been scored against the configured resume."""

    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    link = Column(String, unique=True, nullable=False)
    description = Column(Text)
    portal = Column(String, default="Unknown")
    search_query = Column(String)
    location = Column(String)
    score = Column(Float)
    reason = Column(Text)
    low_match_reason = Column(Text)
    match_category = Column(String)
    skills = Column(String)  # Comma-separated string of top 5 skills
    cover_letter_path = Column(String)
    applied = Column(Boolean, default=False)
    language_required = Column(String)  # e.g., "German" if mandatory, else empty
    salary = Column(String)  # Salary range if provided

engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
Base.metadata.create_all(engine)


def ensure_schema():
    """Add newly introduced columns when an older SQLite DB already exists."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    required_columns = {
        "portal": "VARCHAR DEFAULT 'Unknown'",
        "search_query": "VARCHAR",
        "location": "VARCHAR",
        "low_match_reason": "TEXT",
        "match_category": "VARCHAR",
        "cover_letter_path": "VARCHAR",
    }
    with engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(jobs)")).fetchall()
        }
        for column_name, column_type in required_columns.items():
            if column_name not in existing:
                connection.execute(
                    text(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
                )


ensure_schema()
Session = sessionmaker(bind=engine)
session = Session()
