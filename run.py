import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

flask_app = create_app()

if __name__ == '__main__':
    # async_mode='threading' in SocketIO means werkzeug handles everything.
    # We use flask_app.run() directly to avoid flask_socketio's internal
    # `app.debug` expression clashing with our `app` package name.
    flask_app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)



