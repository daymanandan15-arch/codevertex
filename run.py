import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db, socketio

from app.models.roadmap import Roadmap
from generate_roadmaps import seed_roadmaps

flask_app = create_app()
app = flask_app  # Alias for Gunicorn in Dockerfile

with flask_app.app_context():
    # Ensure tables are created automatically on empty production databases
    db.create_all()
    
    # Auto-seed if empty (e.g., fresh Postgres on Render)
    try:
        if not Roadmap.query.first():
            print("Auto-seeding roadmaps...")
            seed_roadmaps()
    except Exception as e:
        print(f"Skipping auto-seed due to error: {e}")

if __name__ == '__main__':

    # async_mode='threading' in SocketIO means werkzeug handles everything.
    socketio.run(flask_app, host='0.0.0.0', port=5000, use_reloader=False)





