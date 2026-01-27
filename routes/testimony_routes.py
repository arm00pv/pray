from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_babel import _, force_locale
from models import Testimony, Praise, Notification, User
from extensions import db, login_manager
from utils import ProfanityFilter, send_email

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
        flash(_('Content is required.'))
        return redirect(url_for('testimony.index'))

    pf = ProfanityFilter()
    if pf.is_profane(content):
        flash(_('Content contains profanity.'))
        return redirect(url_for('testimony.index'))

    testimony = Testimony(user_id=current_user.id, content=content)
    db.session.add(testimony)
    db.session.commit()
    flash(_('Testimony shared successfully.'))
    return redirect(url_for('testimony.index'))

@testimony_bp.route('/praise/<int:testimony_id>', methods=['POST'])
@login_required
def toggle_praise(testimony_id):
    testimony = Testimony.query.get_or_404(testimony_id)

    existing = Praise.query.filter_by(user_id=current_user.id, testimony_id=testimony_id).first()

    if existing:
        db.session.delete(existing)
        message = _('Praise removed.')
    else:
        praise = Praise(user_id=current_user.id, testimony_id=testimony_id)
        db.session.add(praise)

        if testimony.user_id != current_user.id:
            author = User.query.get(testimony.user_id)
            with force_locale(author.preferred_language or 'en'):
                notif_msg = _("%(username)s praised your testimony.", username=current_user.username)
                email_subject = _("New Praise on your Testimony")
                email_body = _("%(username)s praised your testimony.", username=current_user.username)

            notif = Notification(user_id=testimony.user_id, message=notif_msg)
            db.session.add(notif)

            if author and author.email:
                send_email(author.email, email_subject, email_body)

    db.session.commit()
    return redirect(request.referrer or url_for('testimony.index'))
@testimony_bp.route('/timeline')
def timeline():
    testimonies = Testimony.query.order_by(Testimony.created_at.desc()).all()
    return render_template('timeline.html', testimonies=testimonies)
