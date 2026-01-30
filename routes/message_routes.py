from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, PrivateMessage, Notification, UserBlock
from extensions import db
from datetime import datetime, timezone
from flask_babel import _, force_locale
from sqlalchemy import or_, and_, func

message_bp = Blueprint('message', __name__, url_prefix='/messages')

@message_bp.route('/inbox')
@login_required
def inbox():
    # Subquery to find the latest message ID for each conversation
    # We want conversations where current_user is either sender or recipient

    # This is a bit complex in pure SQLAlchamy, simpler approach:
    # Fetch all messages involving the user, order by date desc
    messages = PrivateMessage.query.filter(
        or_(PrivateMessage.sender_id == current_user.id, PrivateMessage.recipient_id == current_user.id)
    ).order_by(PrivateMessage.created_at.desc()).all()

    conversations = {}
    for msg in messages:
        other_user_id = msg.sender_id if msg.sender_id != current_user.id else msg.recipient_id
        if other_user_id not in conversations:
            other_user = User.query.get(other_user_id)
            conversations[other_user_id] = {
                'user': other_user,
                'last_message': msg,
                'unread_count': 0
            }

        if msg.recipient_id == current_user.id and not msg.is_read:
            conversations[other_user_id]['unread_count'] += 1

    # Convert dict to list and sort by last message date
    conv_list = sorted(conversations.values(), key=lambda x: x['last_message'].created_at, reverse=True)

    return render_template('messages/inbox.html', conversations=conv_list)

@message_bp.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
@login_required
def conversation(user_id):
    other_user = User.query.get_or_404(user_id)

    # Check blocking
    is_blocked = UserBlock.query.filter_by(blocker_id=other_user.id, blocked_id=current_user.id).first()
    i_blocked = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=other_user.id).first()

    if request.method == 'POST':
        if is_blocked:
            flash(_('You cannot send messages to this user.'))
        elif i_blocked:
            flash(_('You must unblock this user to send messages.'))
        else:
            content = request.form.get('content')
            if content:
                msg = PrivateMessage(
                    sender_id=current_user.id,
                    recipient_id=other_user.id,
                    content=content
                )
                db.session.add(msg)

                # Create notification
                with force_locale(other_user.preferred_language or 'en'):
                    notif_msg = _("New message from %(username)s", username=current_user.username)

                notif = Notification(
                    user_id=other_user.id,
                    message=notif_msg
                )
                db.session.add(notif)

                db.session.commit()
                return redirect(url_for('message.conversation', user_id=user_id))

    # Mark messages as read
    unread_msgs = PrivateMessage.query.filter_by(
        sender_id=user_id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for msg in unread_msgs:
        msg.is_read = True
    db.session.commit()

    # Fetch conversation history
    messages = PrivateMessage.query.filter(
        or_(
            and_(PrivateMessage.sender_id == current_user.id, PrivateMessage.recipient_id == other_user.id),
            and_(PrivateMessage.sender_id == other_user.id, PrivateMessage.recipient_id == current_user.id)
        )
    ).order_by(PrivateMessage.created_at.asc()).all()

    return render_template('messages/conversation.html', other_user=other_user, messages=messages)

@message_bp.route('/send/<int:user_id>', methods=['POST'])
@login_required
def send_quick(user_id):
    # Route for "Send Message" button from profile

    # Check blocking
    is_blocked = UserBlock.query.filter_by(blocker_id=user_id, blocked_id=current_user.id).first()
    i_blocked = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user_id).first()

    if is_blocked:
        flash(_('You cannot send messages to this user.'))
        return redirect(url_for('profile.public_profile', username=User.query.get(user_id).username))
    if i_blocked:
        flash(_('You must unblock this user to send messages.'))
        return redirect(url_for('profile.public_profile', username=User.query.get(user_id).username))

    content = request.form.get('content')
    if content:
        msg = PrivateMessage(
            sender_id=current_user.id,
            recipient_id=user_id,
            content=content
        )
        db.session.add(msg)

        # Notify
        recipient = User.query.get(user_id)
        with force_locale(recipient.preferred_language or 'en'):
            notif_msg = _("New message from %(username)s", username=current_user.username)

        notif = Notification(
            user_id=user_id,
            message=notif_msg
        )
        db.session.add(notif)

        db.session.commit()
        flash(_('Message sent.'))
    else:
        flash(_('Message cannot be empty.'))

    return redirect(url_for('message.conversation', user_id=user_id))
