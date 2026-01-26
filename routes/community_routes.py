from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_babel import _, force_locale
from models import PrayerEntry, Amen, Notification, User, Tag
from extensions import db
from utils import send_email
from sqlalchemy import or_


community_bp = Blueprint('community', __name__, url_prefix='/community')

@community_bp.route('/')
def index():
    q = request.args.get('q')
    query = PrayerEntry.query.filter_by(is_public=True, is_hidden=False)

    if q:
        search = f"%{q}%"
        query = query.outerjoin(PrayerEntry.tags).filter(
            or_(
                PrayerEntry.content.ilike(search),
                Tag.name.ilike(search)
            )
        )

    entries = query.order_by(PrayerEntry.created_at.desc()).all()
    return render_template('community.html', entries=entries)

@community_bp.route('/flag/<int:entry_id>', methods=['POST'])
@login_required
def flag_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    entry.flag_count += 1
    entry.is_hidden = True  # Auto-hide on flag
    db.session.commit()
    flash(_('Entry flagged for review.'))
    return redirect(url_for('community.index'))

@community_bp.route('/amen/<int:entry_id>', methods=['POST'])
@login_required
def toggle_amen(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)

    # Check if already amened
    existing = Amen.query.filter_by(user_id=current_user.id, entry_id=entry_id).first()

    if existing:
        db.session.delete(existing)
        message = _('Amen removed.')
    else:
        amen = Amen(user_id=current_user.id, entry_id=entry_id)
        db.session.add(amen)
        message = _('Amen added.')

        # Notify author if not self
        if entry.user_id != current_user.id:
            # Prepare notification message (stored in DB, usually displayed in user's UI context,
            # but if we want it to be localized for recipient, we should store key or force locale if stored as text.
            # Storing as text means it's baked in sender's language or server language.
            # Best practice is storing key + params, but for now we bake it using recipient's pref if possible,
            # or just generic. Actually, notifications in UI are usually translated at render time if structured.
            # Since we store 'message' string, let's try to translate it to recipient's language.

            author = User.query.get(entry.user_id)

            with force_locale(author.preferred_language or 'en'):
                notif_msg = _("%(username)s said Amen to your prayer.", username=current_user.username)
                email_subject = _("Someone prayed with you")
                email_body = _("%(username)s said Amen to your prayer: '%(content)s...'", username=current_user.username, content=entry.content[:50])

            notif = Notification(user_id=entry.user_id, message=notif_msg)
            db.session.add(notif)

            # Send Email
            if author and author.email:
                send_email(author.email, email_subject, email_body)

    db.session.commit()
    # Return to referrer or index
    return redirect(request.referrer or url_for('community.index'))
