from app.extensions import db
from datetime import datetime

class JobListing(db.Model):
    __tablename__ = 'job_listings'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))
    url = db.Column(db.String(500), unique=True, nullable=False)
    source_platform = db.Column(db.String(100), nullable=False) # e.g., LinkedIn, Naukri
    posted_at = db.Column(db.DateTime, index=True)
    is_active = db.Column(db.Boolean, default=True)
    # Comma-separated required skill tags, e.g. "python,sql,docker"
    required_skills = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<JobListing {self.title} at {self.company}>'
