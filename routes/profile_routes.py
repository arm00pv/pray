
from flask import Blueprint, render_template, abort, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, PrayerEntry, Testimony, UserBlock
from extensions import db
from flask_babel import _

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/u/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    # Check if blocking relation exists
    is_blocked_by_me = False
    is_blocking_me = False

    if current_user.is_authenticated:
        is_blocked_by_me = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user.id).first() is not None
        is_blocking_me = UserBlock.query.filter_by(blocker_id=user.id, blocked_id=current_user.id).first() is not None

    # Don't show profile details if blocked (optional, or just hide content)
    # For now, we show profile header but hide content if blocked

    # Public prayers
    public_prayers = []
    if not is_blocked_by_me and not is_blocking_me:
        public_prayers = PrayerEntry.query.filter_by(user_id=user.id, is_public=True, is_hidden=False).order_by(PrayerEntry.created_at.desc()).all()

    # Public testimonies
    testimonies = []
    if not is_blocked_by_me and not is_blocking_me:
        testimonies = Testimony.query.filter_by(user_id=user.id).order_by(Testimony.created_at.desc()).all()

    # Stats
    prayer_count = len(public_prayers)
    amen_count = sum([len(p.amens) for p in public_prayers])

    return render_template('public_profile.html',
                           user=user,
                           prayers=public_prayers,
                           testimonies=testimonies,
                           prayer_count=prayer_count,
                           amen_count=amen_count,
                           is_blocked_by_me=is_blocked_by_me)

@profile_bp.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user_to_block = User.query.get_or_404(user_id)
    if user_to_block.id == current_user.id:
        flash(_('You cannot block yourself.'))
        return redirect(url_for('profile.public_profile', username=current_user.username))

    existing = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user_to_block.id).first()
    if not existing:
        block = UserBlock(blocker_id=current_user.id, blocked_id=user_to_block.id)
        db.session.add(block)
        db.session.commit()
        flash(_('User blocked.'))

    return redirect(url_for('profile.public_profile', username=user_to_block.username))

@profile_bp.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user_to_unblock = User.query.get_or_404(user_id)
    existing = UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user_to_unblock.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(_('User unblocked.'))

    return redirect(request.referrer or url_for('profile.public_profile', username=user_to_unblock.username))

@profile_bp.route('/my_profile')
@login_required
def my_profile():
    return redirect(url_for('profile.public_profile', username=current_user.username))
