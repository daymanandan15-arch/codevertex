from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("Syncing new SQLAlchemy models to the MySQL schema...")
    db.create_all()
    print("Database tables created successfully for Roadmaps and Community Forums.")
