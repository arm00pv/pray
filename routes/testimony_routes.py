from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Testimony
from extensions import db
from utils import ProfanityFilter

testimony_bp = Blueprint('testimony', __name__, url_prefix='/testimonies')

@testimony_bp.route('/')
def index():
    testimonies = Testimony.query.order_by(Testimony.created_at.desc()).all()
    return render_template('testimonies.html', testimonies=testimonies)

@testimony_bp.route('/add', methods=['POST'])
@login_required
def add_testimony():
    content = request.form.get('content')
    if not content:
        flash('Content is required.')
        return redirect(url_for('testimony.index'))

    pf = ProfanityFilter()
    if pf.is_profane(content):
        flash('Content contains profanity.')
        return redirect(url_for('testimony.index'))

    testimony = Testimony(user_id=current_user.id, content=content)
    db.session.add(testimony)
    db.session.commit()
    flash('Testimony shared successfully.')
    return redirect(url_for('testimony.index'))
