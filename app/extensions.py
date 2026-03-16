from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
scheduler = BackgroundScheduler()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
