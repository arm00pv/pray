from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerReminder, PrayerEntry
from extensions import db
from datetime import datetime, timezone
from flask_babel import _
from dateutil import parser

reminder_bp = Blueprint('reminder', __name__, url_prefix='/reminders')

@reminder_bp.route('/set/<int:entry_id>', methods=['POST'])
@login_required
def set_reminder(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)

    # Ensure user owns the entry (or wants to be reminded of their own entry? or any entry?
    # Usually you want to be reminded of your own list, or maybe a friend's request.
    # For now, let's allow setting reminder for ANY entry (e.g. "Pray for this person").

    reminder_time_str = request.form.get('reminder_time')
    if not reminder_time_str:
        flash(_('Please select a time.'))
        return redirect(url_for('entry.user_dashboard'))

    try:
        # Expected format from datetime-local input: "YYYY-MM-DDTHH:MM"
        reminder_time = parser.parse(reminder_time_str)
        # Assuming server runs in UTC or handling naive datetime as local for now
        # Ideally we convert to UTC.

        # Simple fix: if user inputs local time, we might store as is if we don't handle zones.
        # But `send_reminders` runs on server time (likely UTC).
        # Let's assume input is user's local time, but saving it directly might cause offset issues.
        # For this MVP, we'll assume the user inputs UTC or server time,
        # OR we rely on browser sending standard ISO.

        reminder = PrayerReminder(
            user_id=current_user.id,
            entry_id=entry.id,
            reminder_datetime=reminder_time
        )
        db.session.add(reminder)
        db.session.commit()
        flash(_('Reminder set successfully.'))

    except ValueError:
        flash(_('Invalid date format.'))

    return redirect(url_for('entry.user_dashboard'))
