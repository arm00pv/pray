from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerGroup, User, GroupJoinRequest, GroupPoll, GroupPollOption, GroupPollVote, GroupEvent
from extensions import db
import secrets
from datetime import datetime

group_bp = Blueprint('group', __name__, url_prefix='/groups')

@group_bp.route('/')
@login_required
def list_groups():
    # my_groups = current_user.prayer_groups
    # We need to construct a list that includes role info for the template
    groups_data = []
    for group in current_user.prayer_groups:
        role = 'member'
        if current_user in group.admins:
            role = 'admin'
        groups_data.append({'group': group, 'role': role})

    return render_template('groups/list.html', my_groups=groups_data)

@group_bp.route('/create', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        flash('Group name is required.')
        return redirect(url_for('group.list_groups'))

    # Check if name exists
    if PrayerGroup.query.filter_by(name=name).first():
        flash('Group name already taken.')
        return redirect(url_for('group.list_groups'))

    # Generate unique code
    code = secrets.token_hex(4) # 8 chars

    group = PrayerGroup(
        name=name,
        description=description,
        code=code,
        created_by=current_user.id
    )
    db.session.add(group)
    db.session.commit()

    # Add creator as admin and member
    group.members.append(current_user)
    group.admins.append(current_user)
    db.session.commit()

    flash(f'Group "{name}" created! Share code: {code}')
    return redirect(url_for('group.view_group', group_id=group.id))

@group_bp.route('/<int:group_id>/events/create', methods=['POST'])
@login_required
def create_event(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user not in group.admins:
        flash('Only admins can create events.')
        return redirect(url_for('group.view_group', group_id=group.id))

    title = request.form.get('title')
    description = request.form.get('description')
    date_str = request.form.get('event_datetime')

    if not title or not date_str:
        flash('Title and Date are required.')
        return redirect(url_for('group.view_group', group_id=group.id))

    try:
        event_dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date format.')
        return redirect(url_for('group.view_group', group_id=group.id))

    event = GroupEvent(
        group_id=group.id,
        created_by=current_user.id,
        title=title,
        description=description,
        event_datetime=event_dt
    )
    db.session.add(event)
    db.session.commit()
    flash('Event scheduled.')
    return redirect(url_for('group.view_group', group_id=group.id))

@group_bp.route('/<int:group_id>')
@login_required
def view_group(group_id):
    group = PrayerGroup.query.get_or_404(group_id)

    if current_user not in group.members:
        flash('You are not a member of this group.')
        return redirect(url_for('group.list_groups'))

    # Determine role
    role = 'member'
    if current_user in group.admins:
        role = 'admin'

    # List members with roles
    members_data = []
    for user in group.members:
        mem_role = 'member'
        if user in group.admins:
            mem_role = 'admin'
        members_data.append({'user': user, 'role': mem_role})

    return render_template('groups/view.html', group=group, members=members_data, current_role=role)

@group_bp.route('/join', methods=['POST'])
@login_required
def join_group():
    code = request.form.get('code')
    if not code:
        flash('Please enter a code.')
        return redirect(url_for('group.list_groups'))

    group = PrayerGroup.query.filter_by(code=code).first()
    if not group:
        flash('Invalid group code.')
        return redirect(url_for('group.list_groups'))

    if current_user in group.members:
        flash('You are already a member.')
        return redirect(url_for('group.view_group', group_id=group.id))

    group.members.append(current_user)
    db.session.commit()

    flash(f'Joined {group.name}!')
    return redirect(url_for('group.view_group', group_id=group.id))

@group_bp.route('/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    group = PrayerGroup.query.get_or_404(group_id)

    if current_user in group.members:
        group.members.remove(current_user)
        if current_user in group.admins:
            group.admins.remove(current_user)
        db.session.commit()
        flash('You left the group.')

    return redirect(url_for('group.list_groups'))

@group_bp.route('/<int:group_id>/polls/create', methods=['POST'])
@login_required
def create_poll(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    if current_user not in group.admins:
        flash('Only admins can create polls.')
        return redirect(url_for('group.view_group', group_id=group.id))

    question = request.form.get('question')
    options_str = request.form.get('options') # Comma separated

    if not question or not options_str:
        flash('Question and options are required.')
        return redirect(url_for('group.view_group', group_id=group.id))

    poll = GroupPoll(group_id=group.id, created_by=current_user.id, question=question)
    db.session.add(poll)
    db.session.flush() # Get ID

    options = [opt.strip() for opt in options_str.split(',') if opt.strip()]
    for opt_text in options:
        option = GroupPollOption(poll_id=poll.id, text=opt_text)
        db.session.add(option)

    db.session.commit()
    flash('Poll created.')
    return redirect(url_for('group.view_group', group_id=group.id))

@group_bp.route('/polls/<int:poll_id>/vote', methods=['POST'])
@login_required
def vote_poll(poll_id):
    poll = GroupPoll.query.get_or_404(poll_id)
    group = poll.group

    if current_user not in group.members:
        flash('Unauthorized.')
        return redirect(url_for('group.list_groups'))

    option_id = request.form.get('option_id')
    if not option_id:
        flash('Please select an option.')
        return redirect(url_for('group.view_group', group_id=group.id))

    # Check if already voted
    existing_vote = GroupPollVote.query.filter_by(poll_id=poll.id, user_id=current_user.id).first()
    if existing_vote:
        existing_vote.option_id = option_id # Update vote
        flash('Vote updated.')
    else:
        vote = GroupPollVote(poll_id=poll.id, user_id=current_user.id, option_id=option_id)
        db.session.add(vote)
        flash('Vote recorded.')

    db.session.commit()
    return redirect(url_for('group.view_group', group_id=group.id))
