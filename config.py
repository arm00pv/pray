import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this-in-prod'

    uri = os.environ.get('DATABASE_URL') or 'sqlite:///praying_diary.db'
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mailgun Configuration
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN')
    MAILGUN_BASE_URL = os.environ.get('MAILGUN_BASE_URL') or 'https://api.mailgun.net/v3'

    # Push Notifications (VAPID)
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '_UuGoF2K3EIzcdo20sm0dXuJ7cNMDUq6mUA4bIBYC98')
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'BLgq3kZvM9FfjeL_MGYGWUDGtvBnji0Vzxocat977geDkD4lp9zf_WYF0PWHmrhgnsOy0IN0jrQ0kI1NQwM5AkU')
    VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL', 'admin@prayingdiary.com')
