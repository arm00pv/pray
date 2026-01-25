from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerGroup
from extensions import db

group_bp = Blueprint('group', __name__, url_prefix='/groups')

@group_bp.route('/')
def index():
    groups = PrayerGroup.query.order_by(PrayerGroup.created_at.desc()).all()
    return render_template('groups.html', groups=groups)

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
    db.session.add(group)
    db.session.commit()
    flash('Prayer group created.')
    return redirect(url_for('group.index'))

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
