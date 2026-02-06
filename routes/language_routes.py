from flask import Blueprint, session, redirect, request, url_for

language_bp = Blueprint('language', __name__)

@language_bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['en', 'es']:
        session['language'] = lang_code
    return redirect(request.referrer or url_for('entry.user_dashboard'))
