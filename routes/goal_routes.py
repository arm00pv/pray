from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import SpiritualGoal
from extensions import db
from datetime import datetime, timezone

goal_bp = Blueprint('goal', __name__, url_prefix='/goals')

@goal_bp.route('/add', methods=['POST'])
@login_required
def add_goal():
    goal_type = request.form.get('goal_type')
    target_count = request.form.get('target_count', type=int)

    if not goal_type or not target_count:
        flash('Invalid goal data.')
        return redirect(url_for('entry.user_dashboard'))

    goal = SpiritualGoal(user_id=current_user.id, goal_type=goal_type, target_count=target_count)
    db.session.add(goal)
    db.session.commit()
    flash('Goal set!')
    return redirect(url_for('entry.user_dashboard'))

@goal_bp.route('/increment/<int:goal_id>', methods=['POST'])
@login_required
def increment_goal(goal_id):
    goal = SpiritualGoal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        return redirect(url_for('entry.user_dashboard'))

    goal.current_count += 1
    db.session.commit()

    if goal.current_count >= goal.target_count:
        flash(f'Congratulations! You reached your goal: {goal.goal_type}!')

    return redirect(url_for('entry.user_dashboard'))
