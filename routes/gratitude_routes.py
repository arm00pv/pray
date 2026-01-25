from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import GratitudeEntry
from extensions import db

gratitude_bp = Blueprint('gratitude', __name__, url_prefix='/gratitude')

@gratitude_bp.route('/')
@login_required
def index():
    entries = GratitudeEntry.query.filter_by(user_id=current_user.id).order_by(GratitudeEntry.created_at.desc()).all()
    return render_template('gratitude.html', entries=entries)

@gratitude_bp.route('/add', methods=['POST'])
@login_required
def add_entry():
    content = request.form.get('content')
    if content:
        entry = GratitudeEntry(user_id=current_user.id, content=content)
        db.session.add(entry)
        db.session.commit()
        flash('Gratitude entry added.')
    return redirect(url_for('gratitude.index'))

@gratitude_bp.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = GratitudeEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('gratitude.index'))

    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.')
    return redirect(url_for('gratitude.index'))
