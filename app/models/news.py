from app.extensions import db
from datetime import datetime

class NewsItem(db.Model):
    __tablename__ = 'news_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    source = db.Column(db.String(100), nullable=False) # e.g., HackerNews, TechCrunch
    published_at = db.Column(db.DateTime, index=True)
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NewsItem {self.title[:20]}...>'
