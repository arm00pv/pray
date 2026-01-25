
from flask import Blueprint, render_template, abort
from models import User, PrayerEntry, Testimony

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/u/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    # Public prayers
    public_prayers = PrayerEntry.query.filter_by(user_id=user.id, is_public=True, is_hidden=False).order_by(PrayerEntry.created_at.desc()).all()

    # Public testimonies (Testimonies are implicitly public if shared?)
    # Let's assume testimonies are public for now as per functionality
    testimonies = Testimony.query.filter_by(user_id=user.id).order_by(Testimony.created_at.desc()).all()

    # Stats
    prayer_count = len(public_prayers)
    amen_count = sum([len(p.amens) for p in public_prayers])

    return render_template('public_profile.html',
                           user=user,
                           prayers=public_prayers,
                           testimonies=testimonies,
                           prayer_count=prayer_count,
                           amen_count=amen_count)
