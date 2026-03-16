from flask import Flask
from config import Config
from app.extensions import db, scheduler

def create_app(config_class=Config):
    # Use `flask_app` instead of `app` to prevent `import app.events` from
    # overwriting the Flask instance with the `app` package module.
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Extension binding
    from app.extensions import db, scheduler, login_manager, socketio
    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    socketio.init_app(flask_app)
    
    # Register single catch-all blueprint
    from app.views import bp as views_bp
    flask_app.register_blueprint(views_bp)

    # Initialize Background Scheduler
    from app.tasks import init_scheduler
    if not scheduler.running:
        init_scheduler(scheduler, flask_app)
        scheduler.start()

    # Diagnostic routing
    @flask_app.route('/health')
    def health_check():
        return {"status": "healthy", "message": "Engineering Portal App Factory Active"}

    # Attach WebSocket event handlers
    import app.events  # noqa: F401

    return flask_app

