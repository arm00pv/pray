from flask import Blueprint, redirect, url_for, flash, request, render_template
from flask_login import login_required, current_user
from models import Notification
from extensions import db

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')

@notification_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=20)
    return render_template('notifications.html', notifications=notifications)

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
    flash('All notifications marked as read.')
    return redirect(request.referrer or url_for('notification.index'))

@notification_bp.route('/delete/<int:notification_id>')
@login_required
def delete(notification_id):
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('notification.index'))

    db.session.delete(notif)
    db.session.commit()
    return redirect(request.referrer or url_for('notification.index'))

@notification_bp.route('/delete_all')
@login_required
def delete_all():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All notifications deleted.')
    return redirect(url_for('notification.index'))
