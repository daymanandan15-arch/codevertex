import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from the .env file explicitly
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    # Fallback to sqlite if DB URI is not found, to prevent hard crashes during scaffolding
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'engineering_portal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
