from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerGroup, GroupMessage, User, GroupEvent
from extensions import db, bcrypt # bcrypt not needed unless verifying passwords, but db is.
from datetime import datetime
from flask_babel import _

group_bp = Blueprint('group', __name__, url_prefix='/groups')

@group_bp.route('/')
def index():
    groups = PrayerGroup.query.order_by(PrayerGroup.created_at.desc()).all()
    return render_template('groups.html', groups=groups)

@group_bp.route('/<int:group_id>')
@login_required
def detail(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user not in group.members:
        flash('You must join the group to view details.')
        return redirect(url_for('group.index'))

    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.created_at.asc()).all()

    # Filter future events
    events = GroupEvent.query.filter(
        GroupEvent.group_id == group_id,
        GroupEvent.event_datetime >= datetime.utcnow()
    ).order_by(GroupEvent.event_datetime.asc()).all()

    return render_template('group_detail.html', group=group, messages=messages, events=events)

@group_bp.route('/<int:group_id>/events/create', methods=['POST'])
@login_required
def create_event(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user not in group.admins:
        flash(_('Only admins can create events.'))
        return redirect(url_for('group.detail', group_id=group.id))

    title = request.form.get('title')
    description = request.form.get('description')
    datetime_str = request.form.get('event_datetime')

    if title and datetime_str:
        try:
            event_dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
            event = GroupEvent(
                group_id=group.id,
                created_by=current_user.id,
                title=title,
                description=description,
                event_datetime=event_dt
            )
            db.session.add(event)
            db.session.commit()
            flash(_('Event created.'))
        except ValueError:
            flash(_('Invalid date format.'))

    return redirect(url_for('group.detail', group_id=group.id))

@group_bp.route('/create', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        flash('Group name is required.')
        return redirect(url_for('group.index'))

    group = PrayerGroup(name=name, description=description, created_by=current_user.id)
    group.members.append(current_user)
    group.admins.append(current_user) # Creator is admin
    db.session.add(group)
    db.session.commit()
    flash('Prayer group created.')
    return redirect(url_for('group.index'))

@group_bp.route('/<int:group_id>/message', methods=['POST'])
@login_required
def post_message(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user not in group.members:
        return redirect(url_for('group.index'))

    content = request.form.get('content')
    if content:
        msg = GroupMessage(group_id=group.id, user_id=current_user.id, content=content)
        db.session.add(msg)
        db.session.commit()
        # Here we could trigger notifications for group members
    return redirect(url_for('group.detail', group_id=group_id))

@group_bp.route('/<int:group_id>/promote/<int:user_id>', methods=['POST'])
@login_required
def promote_member(group_id, user_id):
    group = PrayerGroup.query.get_or_404(group_id)

    if current_user not in group.admins:
        flash('Only group admins can promote members.')
        return redirect(url_for('group.detail', group_id=group_id))

    member = User.query.get_or_404(user_id)
    if member in group.members and member not in group.admins:
        group.admins.append(member)
        db.session.commit()
        flash(f'{member.username} promoted to admin.')

    return redirect(url_for('group.detail', group_id=group_id))

@group_bp.route('/join/<int:group_id>', methods=['POST'])
@login_required
def join_group(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user not in group.members:
        group.members.append(current_user)
        db.session.commit()
        flash(f'Joined group {group.name}.')
    return redirect(url_for('group.index'))

@group_bp.route('/leave/<int:group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user in group.members:
        group.members.remove(current_user)
        db.session.commit()
        flash(f'Left group {group.name}.')
    return redirect(url_for('group.index'))
