from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import PushSubscription
from extensions import db
import json
from pywebpush import webpush, WebPushException

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')

@notification_bp.route('/', methods=['GET'])
@login_required
def index():
    # Placeholder for full notifications page if needed
    from flask import render_template
    return render_template('notifications.html')

@notification_bp.route('/mark_read/<int:notification_id>')
@login_required
def mark_read(notification_id):
    from models import Notification
    from flask import redirect, url_for, request as req

    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        return redirect(url_for('index'))

    notif.is_read = True
    db.session.commit()
    return redirect(req.referrer or url_for('index'))

@notification_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    data = request.get_json()
    if not data or 'endpoint' not in data or 'keys' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid subscription data'}), 400

    endpoint = data['endpoint']
    keys = data['keys']
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')

    # Check if exists
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        if existing.user_id != current_user.id:
             existing.user_id = current_user.id # Update ownership if needed
             db.session.commit()
        return jsonify({'status': 'success', 'message': 'Already subscribed'})

    new_sub = PushSubscription(
        user_id=current_user.id,
        endpoint=endpoint,
        keys_p256dh=p256dh,
        keys_auth=auth
    )
    db.session.add(new_sub)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Subscribed successfully'})

@notification_bp.route('/test_push', methods=['POST'])
@login_required
def test_push():
    # Send to current user
    subscriptions = PushSubscription.query.filter_by(user_id=current_user.id).all()
    count = 0

    payload = json.dumps({
        'title': 'Praying Diary',
        'body': 'This is a test notification!',
        'url': url_for('entry.user_dashboard', _external=True)
    })

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.keys_p256dh,
                        "auth": sub.keys_auth
                    }
                },
                data=payload,
                vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
                vapid_claims={"sub": "mailto:" + current_app.config['VAPID_CLAIM_EMAIL']}
            )
            count += 1
        except WebPushException as ex:
            print("WebPush Error:", ex)
            # If 410 Gone, remove subscription
            if ex.response and ex.response.status_code == 410:
                db.session.delete(sub)
                db.session.commit()

    return jsonify({'status': 'success', 'sent_count': count})
