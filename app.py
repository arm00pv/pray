from flask import Flask, render_template, redirect, url_for, session, request
from flask_migrate import Migrate
from flask_babel import Babel, force_locale, _
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
from routes.message_routes import message_bp
from routes.reminder_routes import reminder_bp
from routes.goal_routes import goal_bp
from routes.game_routes import game_bp
from routes.feedback_routes import feedback_bp
from routes.reading_routes import reading_bp
from routes.sermon_routes import sermon_bp
from utils import get_random_verse, send_email, get_todays_reading
from utils.gamification import seed_badges
from utils.sticker_helper import count_stickers
from utils.verse_linker import link_bible_verses as link_verses
from utils.prompts import get_daily_prompt
from models import Announcement, PrayerReminder
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

def send_reminders(app):
    """
    Background job to send reminders.
    """
    with app.app_context():
        # 1. Continuous Petitions (Log only for now to avoid spamming in demo)
        continuous_entries = PrayerEntry.query.filter_by(is_continuous=True).all()
        for entry in continuous_entries:
            user = User.query.get(entry.user_id)
            if user and user.email:
                # In real app, check if we already sent one today
                pass

        # 2. Scheduled Reminders
        now = datetime.now()
        due_reminders = PrayerReminder.query.filter(PrayerReminder.is_sent == False, PrayerReminder.reminder_datetime <= now).all()

        for reminder in due_reminders:
            user = reminder.user
            entry = reminder.entry
            if user and user.email and entry:
                # Use user's preferred language
                with force_locale(user.preferred_language or 'en'):
                    subject = _("Prayer Reminder: %(content)s", content=(entry.content[:30] + "..." if len(entry.content) > 30 else entry.content))
                    body = _("Hello %(username)s,\n\nYou asked to be reminded to pray for this request:\n\n%(entry_content)s\n\n- Praying Diary", username=user.username, entry_content=entry.content)

                print(f"Sending reminder to {user.email}")
                if send_email(user.email, subject, body):
                    reminder.is_sent = True
                    db.session.commit()

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
    app.register_blueprint(message_bp)
    app.register_blueprint(reminder_bp)
    app.register_blueprint(goal_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(reading_bp)
    app.register_blueprint(sermon_bp)

    @app.template_filter('render_chat_message')
    def render_chat_message(content):
        # Basic filter to render GIF tags
        import re
        from markupsafe import escape

        # Escape the content first to prevent XSS from user text
        escaped_content = str(escape(content))

        def replace_gif(match):
            url = match.group(1)
            # Basic validation
            if url.startswith('http') or url.startswith('https'):
                return f'<div class="mt-1"><img src="{url}" class="img-fluid rounded" style="max-width: 200px;" alt="GIF"></div>'
            return match.group(0)

        # Replace [GIF:url] with image tag
        return re.sub(r'\[GIF:(.*?)\]', replace_gif, escaped_content)

    @app.template_filter('link_verses')
    def link_verses_filter(content):
        return link_verses(content)

    @app.context_processor
    def inject_context():
        locale = get_locale()
        if not isinstance(locale, str):
             locale = str(locale)

        active_announcement = Announcement.query.filter_by(is_active=True).first()

        # Determine seed key for stable verse
        # Need to import inside function to avoid circular imports or context issues
        from flask_login import current_user

        if current_user.is_authenticated:
            seed_key = str(current_user.id)
        else:
            # Use remote address or session ID for anonymous users
            seed_key = request.remote_addr or session.get('anon_id', 'anonymous')

        # Global Prayer Counter (Today)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        prayers_today = PrayerEntry.query.filter(PrayerEntry.created_at >= today_start).count()

        return dict(
            daily_verse=get_random_verse(locale, seed_key=seed_key),
            daily_prompt=get_daily_prompt(),
            active_announcement=active_announcement,
            reading_plan=get_todays_reading(),
            count_stickers=count_stickers,
            current_year=datetime.now().year,
            prayers_today=prayers_today
        )

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
if not os.environ.get('SKIP_DB_INIT'):
    initialize_db()
    with app.app_context():
        seed_badges()
        print("Badges seeded.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Disable debug mode in production context
    app.run(debug=False, host='0.0.0.0', port=port)
