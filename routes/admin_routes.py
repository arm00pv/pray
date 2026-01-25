from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Tag, PrayerEntry, AdminInvite, BlockedUser, User, CommunityEmail
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

@admin_bp.route('/dashboard/flagged')
def flagged_entries():
    # Show entries that are flagged (and likely hidden)
    entries = PrayerEntry.query.filter(PrayerEntry.flag_count > 0).all()
    return render_template('admin_flagged.html', entries=entries)

@admin_bp.route('/dashboard/emails')
def community_emails():
    emails = CommunityEmail.query.order_by(CommunityEmail.created_at.desc()).all()
    return render_template('admin_emails.html', emails=emails)

@admin_bp.route('/unhide_entry/<int:entry_id>', methods=['POST'])
def unhide_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    entry.is_hidden = False
    entry.flag_count = 0  # Reset flags on approval
    db.session.commit()
    flash('Entry approved and reposted.')
    return redirect(url_for('admin.flagged_entries'))

@admin_bp.route('/block_user/<int:user_id>', methods=['POST'])
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.email:
        if not BlockedUser.query.filter_by(email=user.email).first():
            blocked = BlockedUser(email=user.email, reason="Blocked by admin")
            db.session.add(blocked)
            db.session.commit()
            flash(f'User {user.email} blocked.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/invite', methods=['POST'])
def create_invite():
    code = str(uuid.uuid4())
    invite = AdminInvite(code=code, created_by_admin_id=current_user.id)
    db.session.add(invite)
    db.session.commit()
    flash(f'Invite code created: {code}')
    return redirect(url_for('admin.dashboard'))
