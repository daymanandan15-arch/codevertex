from app.extensions import db, login_manager
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)  # nullable for GitHub OAuth users
    reputation = db.Column(db.Integer, default=0)  # RP points for contributions
    # GitHub OAuth fields
    github_id = db.Column(db.String(50), unique=True, nullable=True)
    github_username = db.Column(db.String(100), nullable=True)
    github_avatar_url = db.Column(db.String(300), nullable=True)
    # Google OAuth fields
    google_id = db.Column(db.String(50), unique=True, nullable=True)
    google_avatar_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Mentorship fields
    is_mentor = db.Column(db.Boolean, default=False)
    mentor_bio = db.Column(db.Text, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
