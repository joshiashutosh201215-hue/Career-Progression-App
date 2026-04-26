from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Base class for declarative models
Base = declarative_base()

# Job model representing the jobs table
class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    link = Column(String, unique=True, nullable=False)
    description = Column(Text)
    score = Column(Float)
    reason = Column(Text)
    skills = Column(String)  # Comma-separated string of top 5 skills
    applied = Column(Boolean, default=False)
    language_required = Column(String)  # e.g., "German" if mandatory, else empty
    salary = Column(String)  # Salary range if provided

# Create SQLite engine
engine = create_engine('sqlite:///jobs.db', echo=False)

# Create all tables
Base.metadata.create_all(engine)

# Create a session factory
Session = sessionmaker(bind=engine)

# Global session instance for use across the application
session = Session()