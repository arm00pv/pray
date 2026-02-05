from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import SermonNote
from extensions import db

sermon_bp = Blueprint('sermon', __name__, url_prefix='/sermons')

@sermon_bp.route('/')
@login_required
def list_sermons():
    notes = SermonNote.query.filter_by(user_id=current_user.id).order_by(SermonNote.created_at.desc()).all()
    return render_template('sermons/list.html', notes=notes)

@sermon_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_sermon():
    if request.method == 'POST':
        title = request.form.get('title')
        preacher = request.form.get('preacher')
        scripture = request.form.get('scripture')
        content = request.form.get('content')

        if not title or not content:
            flash('Title and Content are required.')
            return redirect(url_for('sermon.add_sermon'))

        note = SermonNote(
            user_id=current_user.id,
            title=title,
            preacher=preacher,
            scripture=scripture,
            content=content
        )
        db.session.add(note)
        db.session.commit()
        flash('Sermon note added.')
        return redirect(url_for('sermon.list_sermons'))

    return render_template('sermons/add.html')

@sermon_bp.route('/<int:sermon_id>')
@login_required
def view_sermon(sermon_id):
    note = SermonNote.query.get_or_404(sermon_id)
    if note.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('sermon.list_sermons'))
    return render_template('sermons/view.html', note=note)
