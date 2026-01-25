from flask import Flask, render_template, redirect, url_for, session, request
from flask_migrate import Migrate
from flask_babel import Babel
from config import Config
from extensions import db, login_manager, bcrypt
from models import User, Admin, AdminInvite, PrayerEntry, Tag
from routes.auth_routes import auth_bp
from routes.admin_auth_routes import admin_auth_bp
from routes.entry_routes import entry_bp
from routes.admin_routes import admin_bp
from routes.settings_routes import settings_bp
from routes.analytics_routes import analytics_bp
from routes.community_routes import community_bp
from routes.language_routes import language_bp
from routes.notification_routes import notification_bp
from routes.gratitude_routes import gratitude_bp
from routes.testimony_routes import testimony_bp
from routes.group_routes import group_bp
from routes.profile_routes import profile_bp
from utils import get_random_verse
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def send_reminders(app):
    """
    Background job to send reminders.
    In a real app, this would send emails via SMTP/SendGrid.
    Here, we log to the console.
    """
    with app.app_context():
        # Find continuous petitions
        continuous_entries = PrayerEntry.query.filter_by(is_continuous=True).all()
        for entry in continuous_entries:
            user = User.query.get(entry.user_id)
            if user and user.email:
                print(f"[EMAIL MOCK] Sending reminder to {user.email} for continuous prayer: {entry.content[:30]}...")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate = Migrate(app, db)

    def get_locale():
        return session.get('language', request.accept_languages.best_match(['en', 'es']))

    babel = Babel(app, locale_selector=get_locale)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(entry_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(language_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(gratitude_bp)
    app.register_blueprint(testimony_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(profile_bp)

    @app.context_processor
    def inject_daily_verse():
        locale = get_locale()
        # Fallback if locale is None or complex object
        if not isinstance(locale, str):
             locale = str(locale)
        return dict(daily_verse=get_random_verse(locale))

    # Scheduler
    # Only run scheduler if not in debug/reloader mode to avoid duplicates
    # OR use a lock. For simple testing, we just start it.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = BackgroundScheduler()
        # Run every minute for testing demonstration
        scheduler.add_job(func=lambda: send_reminders(app), trigger="interval", minutes=1)
        scheduler.start()
        print("Scheduler started.")

    @app.route('/')
    def index():
        # Fetch 5 most recent public, non-hidden entries for the live feed
        recent_entries = PrayerEntry.query.filter_by(is_public=True, is_hidden=False)\
            .order_by(PrayerEntry.created_at.desc()).limit(5).all()
        return render_template('index.html', entries=recent_entries)

    return app

app = create_app()

def initialize_db():
    """Initializes the database and creates the master admin if needed."""
    with app.app_context():
        db.create_all() # Ensure tables exist
        if not Admin.query.first():
            print("Creating Master Admin...")
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            master = Admin(username='admin', password_hash=hashed_pw)
            db.session.add(master)
            db.session.commit()
            print("Master Admin created: user=admin, pass=admin123")
        else:
            print("Admin already exists.")

# Ensure DB is initialized in production (Gunicorn)
initialize_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Disable debug mode in production context
    app.run(debug=False, host='0.0.0.0', port=port)
