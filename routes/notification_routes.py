from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Notification
from extensions import db

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')

@notification_bp.route('/read/<int:notification_id>')
@login_required
def mark_read(notification_id):
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    notif.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('entry.user_dashboard'))

@notification_bp.route('/clear')
@login_required
def clear_all():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for('entry.user_dashboard'))
