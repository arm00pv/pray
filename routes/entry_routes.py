from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import PrayerEntry, Tag, entry_tags
from extensions import db
from utils import extract_tags, get_geolocation
import json

entry_bp = Blueprint('entry', __name__)

@entry_bp.route('/dashboard')
@login_required
def user_dashboard():
    # Show user's entries ordered by date desc
    entries = PrayerEntry.query.filter_by(user_id=current_user.id).order_by(PrayerEntry.created_at.desc()).all()
    return render_template('user_dashboard.html', entries=entries)

@entry_bp.route('/add', methods=['POST'])
@login_required
def add_entry():
    content = request.form.get('content')
    if not content:
        flash('Prayer content cannot be empty.')
        return redirect(url_for('entry.user_dashboard'))

    # IP and Geo
    ip = request.remote_addr
    # On some proxies/hosting, use X-Forwarded-For
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]

    geo_data = get_geolocation(ip)

    entry = PrayerEntry(
        user_id=current_user.id,
        content=content,
        ip_address=ip,
        geolocation_data=json.dumps(geo_data) if geo_data else None
    )

    # Tags
    tag_names = extract_tags(content)
    for name in tag_names:
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name, count=1)
            db.session.add(tag)
        else:
            tag.count += 1
        entry.tags.append(tag)

    db.session.add(entry)
    db.session.commit()
    flash('Prayer entry added.')
    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/entry/<int:entry_id>/status', methods=['POST'])
@login_required
def update_status(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    status = request.form.get('status')
    if status in ['active', 'fulfilled', 'dropped']:
        entry.status = status
        db.session.commit()

    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/entry/<int:entry_id>/continuous', methods=['POST'])
@login_required
def toggle_continuous(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    entry.is_continuous = not entry.is_continuous
    db.session.commit()
    return redirect(url_for('entry.user_dashboard'))

@entry_bp.route('/entry/<int:entry_id>/sticker', methods=['POST'])
@login_required
def add_sticker(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('entry.user_dashboard'))

    sticker = request.form.get('sticker')
    if sticker:
        if entry.stickers:
            entry.stickers += f",{sticker}"
        else:
            entry.stickers = sticker
        db.session.commit()

    return redirect(url_for('entry.user_dashboard'))
