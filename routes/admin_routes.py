from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Tag, PrayerEntry, AdminInvite
from extensions import db
import json
import uuid

admin_bp = Blueprint('admin', __name__, url_prefix='/admins')

@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated or not current_user.get_id().startswith('admin_'):
        return redirect(url_for('admin_auth.login'))

@admin_bp.route('/dashboard')
def dashboard():
    # Metrics: Most mentioned petitions
    top_tags = Tag.query.order_by(Tag.count.desc()).limit(10).all()

    # Metrics: IP locations
    # Get all entries with geo data
    entries = PrayerEntry.query.filter(PrayerEntry.geolocation_data != None).all()
    locations = []
    for e in entries:
        try:
            data = json.loads(e.geolocation_data)
            if data and 'lat' in data and 'lon' in data:
                locations.append({
                    'lat': data['lat'],
                    'lon': data['lon'],
                    'country': data.get('country'),
                    'city': data.get('city'),
                    'ip': e.ip_address
                })
        except:
            pass

    return render_template('admin_dashboard.html', top_tags=top_tags, locations=locations)

@admin_bp.route('/invite', methods=['POST'])
def create_invite():
    code = str(uuid.uuid4())
    invite = AdminInvite(code=code, created_by_admin_id=current_user.id)
    db.session.add(invite)
    db.session.commit()
    flash(f'Invite code created: {code}')
    return redirect(url_for('admin.dashboard'))
