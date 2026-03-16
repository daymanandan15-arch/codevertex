from app.extensions import db
from datetime import datetime

class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False) # e.g., Course, Playlist, Repo
    url = db.Column(db.String(500), unique=True, nullable=False)
    tags = db.Column(db.String(255)) # Comma separated for simplicity right now
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Resource {self.title} ({self.resource_type})>'
