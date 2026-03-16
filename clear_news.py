from app import create_app
from app.extensions import db
from app.models.news import NewsItem

app = create_app()

with app.app_context():
    print("Flushing heavy Dev.to cache from the database to force fresh diverse ingestion...")
    NewsItem.query.delete()
    db.session.commit()
    print("Database cleared. Next APScheduler run will populate diverse global feeds.")
