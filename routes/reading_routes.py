from flask import Blueprint, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import ReadingProgress
from extensions import db
from datetime import datetime, timezone
from flask_babel import _

reading_bp = Blueprint('reading', __name__, url_prefix='/reading')

@reading_bp.route('/mark_read', methods=['POST'])
@login_required
def mark_read():
    # In a real app, reading plan logic would be dynamic and persisted in DB.
    # For now, we assume today's reading (from utils) is the target.
    # We store progress by date.

    today = datetime.now(timezone.utc).date()
    progress = ReadingProgress.query.filter_by(user_id=current_user.id, reading_date=today).first()

    if not progress:
        progress = ReadingProgress(user_id=current_user.id, reading_date=today, is_completed=True)
        db.session.add(progress)
    else:
        # Toggle
        progress.is_completed = not progress.is_completed

    db.session.commit()

    status = _('marked as read') if progress.is_completed else _('marked as unread')
    flash(_('Reading %(status)s.', status=status))

    return redirect(request.referrer or url_for('entry.user_dashboard'))
