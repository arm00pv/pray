from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from models import PrayerEntry
from extensions import db

community_bp = Blueprint('community', __name__, url_prefix='/community')

@community_bp.route('/')
def index():
    # Show entries marked as public, ordered by date
    entries = PrayerEntry.query.filter_by(is_public=True).order_by(PrayerEntry.created_at.desc()).all()
    return render_template('community.html', entries=entries)

@community_bp.route('/flag/<int:entry_id>', methods=['POST'])
@login_required
def flag_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    entry.flag_count += 1
    db.session.commit()
    flash('Entry flagged for review.')
    return redirect(url_for('community.index'))
