from flask import Blueprint, session, redirect, request, url_for
from flask_login import current_user
from extensions import db

language_bp = Blueprint('language', __name__)

@language_bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'es']:
        session['language'] = lang_code

        if current_user.is_authenticated:
            current_user.preferred_language = lang_code
            db.session.commit()

    return redirect(request.referrer or url_for('entry.user_dashboard'))
