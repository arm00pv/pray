import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///praying_diary.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mailgun Configuration
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN')
    MAILGUN_BASE_URL = os.environ.get('MAILGUN_BASE_URL') or 'https://api.mailgun.net/v3'
