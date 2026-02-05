from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerGroup, GroupMember, User
from extensions import db
import secrets

group_bp = Blueprint('group', __name__, url_prefix='/groups')

@group_bp.route('/')
@login_required
def list_groups():
    my_groups = GroupMember.query.filter_by(user_id=current_user.id).all()
    return render_template('groups/list.html', my_groups=my_groups)

@group_bp.route('/create', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name')
    description = request.form.get('description')

    if not name:
        flash('Group name is required.')
        return redirect(url_for('group.list_groups'))

    # Generate unique code
    code = secrets.token_hex(4) # 8 chars

    group = PrayerGroup(
        name=name,
        description=description,
        code=code,
        created_by_id=current_user.id
    )
    db.session.add(group)
    db.session.commit()

    # Add creator as admin member
    member = GroupMember(user_id=current_user.id, group_id=group.id, role='admin')
    db.session.add(member)
    db.session.commit()

    flash(f'Group "{name}" created! Share code: {code}')
    return redirect(url_for('group.view_group', group_id=group.id))

@group_bp.route('/<int:group_id>')
@login_required
def view_group(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    # Check if member
    member = GroupMember.query.filter_by(user_id=current_user.id, group_id=group.id).first()
    if not member:
        flash('You are not a member of this group.')
        return redirect(url_for('group.list_groups'))

    members = GroupMember.query.filter_by(group_id=group.id).all()
    return render_template('groups/view.html', group=group, members=members, current_member=member)

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

    # Check if already member
    existing = GroupMember.query.filter_by(user_id=current_user.id, group_id=group.id).first()
    if existing:
        flash('You are already a member.')
        return redirect(url_for('group.view_group', group_id=group.id))

    member = GroupMember(user_id=current_user.id, group_id=group.id, role='member')
    db.session.add(member)
    db.session.commit()

    flash(f'Joined {group.name}!')
    return redirect(url_for('group.view_group', group_id=group.id))

@group_bp.route('/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    group = PrayerGroup.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(user_id=current_user.id, group_id=group.id).first()

    if member:
        db.session.delete(member)
        db.session.commit()
        flash('You left the group.')

    return redirect(url_for('group.list_groups'))
