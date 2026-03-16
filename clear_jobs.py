from app import create_app
from app.extensions import db
from app.models.job import JobListing
from datetime import datetime

app = create_app()

with app.app_context():
    print("Forcing direct table trunacate...")
    JobListing.query.delete()
    db.session.commit()
    
    # Direct insertion
    mock_jobs = [
            {'title': 'Senior React Engineer (India)', 'company': 'Techflow India', 'location': 'Remote / Bangalore', 'url': 'https://example.com/job1', 'plat': 'LinkedIn API'},
            {'title': 'Django Backend Developer', 'company': 'Global Systems', 'location': 'Pune, India', 'url': 'https://example.com/job2', 'plat': 'Naukri'},
            {'title': 'Cloud Architect (AWS)', 'company': 'CloudNative Inc.', 'location': 'Remote / India', 'url': 'https://example.com/job3', 'plat': 'LinkedIn API'},
            {'title': 'Frontend Engineer (Vue.js)', 'company': 'Innovate AI', 'location': 'Hyderabad, India', 'url': 'https://example.com/job4', 'plat': 'AngelList'},
            {'title': 'Data Scientist', 'company': 'Quant Analytics', 'location': 'Delhi / Remote', 'url': 'https://example.com/job5', 'plat': 'Naukri'},
            {'title': 'DevOps Engineer', 'company': 'SecureNet', 'location': 'Mumbai, India', 'url': 'https://example.com/job6', 'plat': 'LinkedIn API'}
        ]
        
    for j in mock_jobs:
        job_obj = JobListing(
            title=j['title'],
            company=j['company'],
            location=j['location'],
            url=j['url']+str(datetime.now().timestamp()), # Force Unique URL
            source_platform=j['plat'],
            posted_at=datetime.utcnow()
        )
        db.session.add(job_obj)
        
    db.session.commit()
    print("Database seeded with fresh Indian tech roles.")
