from flask import Blueprint, render_template
from models import PrayerEntry

community_bp = Blueprint('community', __name__, url_prefix='/community')

@community_bp.route('/')
def index():
    # Show entries marked as public, ordered by date
    entries = PrayerEntry.query.filter_by(is_public=True).order_by(PrayerEntry.created_at.desc()).all()
    return render_template('community.html', entries=entries)
