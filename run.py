import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db

flask_app = create_app()
app = flask_app  # Alias for Gunicorn in Dockerfile

with flask_app.app_context():

    # Ensure tables are created automatically on empty production databases
    db.create_all()

if __name__ == '__main__':
    # async_mode='threading' in SocketIO means werkzeug handles everything.
    flask_app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)




