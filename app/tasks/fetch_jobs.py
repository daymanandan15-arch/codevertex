from datetime import datetime

def fetch_and_store_jobs(app):
    """
    Called by APScheduler — receives the *already created* Flask app instance.
    Uses mock seed data for India-focused listings during MVP.
    """
    from app.extensions import db
    from app.models.job import JobListing

    MOCK_JOBS = [
        {'title': 'Senior Python Backend Engineer',  'company': 'Techflow India',    'location': 'Remote / Bangalore', 'url': 'https://example.com/job5172906725', 'plat': 'LinkedIn'},
        {'title': 'Full Stack Developer (React/Node)','company': 'Global Systems',    'location': 'Pune, India',        'url': 'https://example.com/job5172906726', 'plat': 'Naukri'},
        {'title': 'Cloud Architect (AWS)',            'company': 'CloudNative Inc.',  'location': 'Remote / India',     'url': 'https://example.com/job5172906727', 'plat': 'LinkedIn'},
        {'title': 'Frontend Engineer (Vue.js)',       'company': 'Innovate AI',       'location': 'Hyderabad, India',   'url': 'https://example.com/job5172906728', 'plat': 'AngelList'},
        {'title': 'Data Scientist',                   'company': 'Quant Analytics',   'location': 'Delhi / Remote',     'url': 'https://example.com/job5172906729', 'plat': 'Naukri'},
        {'title': 'DevOps Engineer',                  'company': 'SecureNet',         'location': 'Mumbai, India',      'url': 'https://example.com/job5172906730', 'plat': 'LinkedIn'},
        {'title': 'Machine Learning Engineer',        'company': 'Neural Labs',       'location': 'Remote / India',     'url': 'https://example.com/job5172906731', 'plat': 'Wellfound'},
        {'title': 'iOS Developer (Swift)',             'company': 'AppCraft',          'location': 'Chennai, India',     'url': 'https://example.com/job5172906732', 'plat': 'LinkedIn'},
        {'title': 'Android Engineer (Kotlin)',         'company': 'MobileFirst',       'location': 'Noida / Remote',     'url': 'https://example.com/job5172906733', 'plat': 'AngelList'},
        {'title': 'Site Reliability Engineer (SRE)',  'company': 'ReliableOps',       'location': 'Bengaluru, India',   'url': 'https://example.com/job5172906734', 'plat': 'LinkedIn'},
        {'title': 'Data Engineer (Spark/Kafka)',       'company': 'DataPipe Labs',     'location': 'Hyderabad / Remote', 'url': 'https://example.com/job5172906735', 'plat': 'Naukri'},
        {'title': 'Security Engineer (Pentesting)',   'company': 'ShieldSec',         'location': 'Remote / India',     'url': 'https://example.com/job5172906736', 'plat': 'LinkedIn'},
    ]

    with app.app_context():
        ts = datetime.utcnow().strftime('%H:%M:%S')
        print(f"[{ts} UTC] APScheduler: fetch_and_store_jobs() START")
        added = 0
        try:
            for j in MOCK_JOBS:
                if not JobListing.query.filter_by(url=j['url']).first():
                    db.session.add(JobListing(
                        title=j['title'][:250],
                        company=j['company'][:150],
                        location=j['location'][:150],
                        url=j['url'][:499],
                        source_platform=j['plat'][:100],
                        posted_at=datetime.utcnow(),
                        is_active=True
                    ))
                    added += 1
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            print(f"  [ERROR] fetch_jobs: {exc}")
        print(f"[{datetime.utcnow().strftime('%H:%M:%S')} UTC] fetch_and_store_jobs() DONE — {added} new listings")
