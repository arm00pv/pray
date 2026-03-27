from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import ReadingProgress
from extensions import db
from datetime import datetime, timezone
from flask_babel import _
from utils.bible_plan import get_plan_for_day

reading_bp = Blueprint('reading', __name__, url_prefix='/reading')

@reading_bp.route('/')
@login_required
def index():
    # Fetch all completed days for the user
    progress = ReadingProgress.query.filter_by(user_id=current_user.id, is_completed=True).all()
    completed_days = {p.plan_day for p in progress if p.plan_day}

    return render_template(
        'reading/index.html',
        completed_days=completed_days,
        completed_count=len(completed_days),
        get_plan=get_plan_for_day
    )

@reading_bp.route('/mark_read', methods=['POST'])
@login_required
def mark_read():
    # Helper for the dashboard "Today's Reading" button
    # Assuming "Today" maps to day of year
    today_day_num = datetime.now().timetuple().tm_yday
    return mark_plan_read(today_day_num)

@reading_bp.route('/mark/<int:day_id>', methods=['POST'])
@login_required
def mark_plan_read(day_id):
    if day_id < 1 or day_id > 366:
        flash(_('Invalid day.'))
        return redirect(url_for('reading.index'))

    # Check if already marked
    entry = ReadingProgress.query.filter_by(user_id=current_user.id, plan_day=day_id).first()

    if not entry:
        entry = ReadingProgress(
            user_id=current_user.id,
            reading_date=datetime.now(timezone.utc).date(),
            plan_day=day_id,
            is_completed=True
        )
        db.session.add(entry)
        msg = _('Day %(day)d marked as read.', day=day_id)
    else:
        # Toggle
        entry.is_completed = not entry.is_completed
        if entry.is_completed:
             msg = _('Day %(day)d marked as read.', day=day_id)
        else:
             msg = _('Day %(day)d marked as unread.', day=day_id)

    db.session.commit()
    flash(msg)

    # Return to where we came from
    return redirect(request.referrer or url_for('reading.index'))
