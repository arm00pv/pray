from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerEntry, Amen, Notification, User
from extensions import db
from utils import send_email


community_bp = Blueprint('community', __name__, url_prefix='/community')

@community_bp.route('/')
def index():
    # Show entries marked as public and NOT hidden, ordered by date
    entries = PrayerEntry.query.filter_by(is_public=True, is_hidden=False).order_by(PrayerEntry.created_at.desc()).all()
    return render_template('community.html', entries=entries)

@community_bp.route('/flag/<int:entry_id>', methods=['POST'])
@login_required
def flag_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    entry.flag_count += 1
    entry.is_hidden = True  # Auto-hide on flag
    db.session.commit()
    flash('Entry flagged for review.')
    return redirect(url_for('community.index'))

@community_bp.route('/amen/<int:entry_id>', methods=['POST'])
@login_required
def toggle_amen(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)

    # Check if already amened
    existing = Amen.query.filter_by(user_id=current_user.id, entry_id=entry_id).first()

    if existing:
        db.session.delete(existing)
        message = 'Amen removed.'
    else:
        amen = Amen(user_id=current_user.id, entry_id=entry_id)
        db.session.add(amen)
        message = 'Amen added.'

        # Notify author if not self
        if entry.user_id != current_user.id:
            notif = Notification(user_id=entry.user_id, message=f"{current_user.username} said Amen to your prayer.")
            db.session.add(notif)

            # Send Email
            author = User.query.get(entry.user_id)
            if author and author.email:
                send_email(
                    author.email,
                    "Someone prayed with you",
                    f"{current_user.username} said Amen to your prayer: '{entry.content[:50]}...'"
                )

    db.session.commit()
    # Return to referrer or index
    return redirect(request.referrer or url_for('community.index'))
