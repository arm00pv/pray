from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import SermonNote
from extensions import db
from flask_babel import _

sermon_bp = Blueprint('sermon', __name__, url_prefix='/sermons')

@sermon_bp.route('/')
@login_required
def index():
    notes = SermonNote.query.filter_by(user_id=current_user.id).order_by(SermonNote.created_at.desc()).all()
    return render_template('sermons/index.html', notes=notes)

@sermon_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        preacher = request.form.get('preacher')
        scripture = request.form.get('scripture_reference')
        content = request.form.get('content')
        takeaways = request.form.get('takeaways')
        tags = request.form.get('tags')

        if not title or not content:
            flash(_('Title and Content are required.'))
            return redirect(url_for('sermon.add'))

        full_content = content
        if takeaways:
            full_content += f"\n\n**Key Takeaways:**\n{takeaways}"
        if tags:
            full_content += f"\n\nTags: {tags}"

        note = SermonNote(
            user_id=current_user.id,
            title=title,
            preacher=preacher,
            scripture_reference=scripture,
            content=full_content
        )
        db.session.add(note)
        db.session.commit()
        flash(_('Sermon note added.'))
        return redirect(url_for('sermon.index'))

    return render_template('sermons/add.html')

@sermon_bp.route('/<int:note_id>')
@login_required
def view(note_id):
    note = SermonNote.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash(_('Unauthorized'))
        return redirect(url_for('sermon.index'))
    return render_template('sermons/view.html', note=note)

@sermon_bp.route('/<int:note_id>/delete', methods=['POST'])
@login_required
def delete(note_id):
    note = SermonNote.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        flash(_('Unauthorized'))
        return redirect(url_for('sermon.index'))

    db.session.delete(note)
    db.session.commit()
    flash(_('Note deleted.'))
    return redirect(url_for('sermon.index'))
