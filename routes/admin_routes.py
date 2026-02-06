from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_babel import _, force_locale
from models import Tag, PrayerEntry, AdminInvite, BlockedUser, User, CommunityEmail, GratitudeEntry, Testimony, PrayerGroup, Announcement, SystemLog, Notification, PrivateMessage, AdminUserNote, Feedback
from extensions import db
import json
import uuid
from sqlalchemy import func
from datetime import datetime, timezone

admin_bp = Blueprint('admin', __name__, url_prefix='/admins')

@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated or not current_user.get_id().startswith('admin_'):
        return redirect(url_for('admin_auth.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Metrics
    total_users = User.query.count()
    total_entries = PrayerEntry.query.count()
    total_gratitude = GratitudeEntry.query.count()
    total_testimonies = Testimony.query.count()
    total_groups = PrayerGroup.query.count()

    # Most mentioned petitions
    top_tags = Tag.query.order_by(Tag.count.desc()).limit(10).all()

    # Flagged entries count
    flagged_count = PrayerEntry.query.filter(PrayerEntry.flag_count > 0).count()

    # Registered Users (Pagination & Search)
    q = request.args.get('q')
    page = request.args.get('page', 1, type=int)

    user_query = User.query
    if q:
        user_query = user_query.filter(User.username.ilike(f'%{q}%') | User.email.ilike(f'%{q}%'))

    users = user_query.order_by(User.created_at.desc()).paginate(page=page, per_page=10)

    # Active Users Today (Users created today OR posted entry today)
    today = datetime.now(timezone.utc).date()
    new_users_today = User.query.filter(func.date(User.created_at) == today).count()
    posting_users_today = db.session.query(PrayerEntry.user_id).filter(func.date(PrayerEntry.created_at) == today).distinct().count()
    active_users_today = new_users_today + posting_users_today # Approximation

    # Metrics: IP locations (Aggregated)
    # Get all entries with geo data
    entries = PrayerEntry.query.filter(PrayerEntry.geolocation_data != None).all()
    locations_map = {}

    for e in entries:
        try:
            data = json.loads(e.geolocation_data)
            ip = e.ip_address
            if data and 'lat' in data and 'lon' in data:
                key = ip
                if key not in locations_map:
                    locations_map[key] = {
                        'lat': data['lat'],
                        'lon': data['lon'],
                        'country': data.get('country'),
                        'region': data.get('regionName'), # State
                        'city': data.get('city'),
                        'ip': ip,
                        'count': 1
                    }
                else:
                    locations_map[key]['count'] += 1
        except:
            pass

    locations = list(locations_map.values())
    locations.sort(key=lambda x: x['count'], reverse=True)

    # System Logs
    logs = SystemLog.query.order_by(SystemLog.created_at.desc()).limit(50).all()

    return render_template('admin_dashboard.html',
                           top_tags=top_tags,
                           locations=locations,
                           flagged_count=flagged_count,
                           total_users=total_users,
                           total_entries=total_entries,
                           total_gratitude=total_gratitude,
                           total_testimonies=total_testimonies,
                           total_groups=total_groups,
                           users=users,
                           logs=logs,
                           active_users_today=active_users_today)

@admin_bp.route('/broadcast', methods=['POST'])
@login_required
def broadcast_message():
    message = request.form.get('message')
    if not message:
        flash(_('Message cannot be empty.'))
        return redirect(url_for('admin.dashboard'))

    # Send to all users
    users = User.query.all()
    count = 0
    for user in users:
        # Create System Notification
        with force_locale(user.preferred_language or 'en'):
            msg_content = f"Admin Broadcast: {message}"

        notif = Notification(
            user_id=user.id,
            message=msg_content
        )
        db.session.add(notif)
        count += 1

    db.session.commit()

    # Log it
    log = SystemLog(level='INFO', message=f"Broadcast sent to {count} users by {current_user.username}")
    db.session.add(log)
    db.session.commit()

    flash(_('Broadcast sent to %(count)d users.', count=count))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard/flagged')
@login_required
def flagged_entries():
    # Show entries that are flagged (and likely hidden)
    entries = PrayerEntry.query.filter(PrayerEntry.flag_count > 0).all()
    return render_template('admin_flagged.html', entries=entries)

@admin_bp.route('/dashboard/emails')
@login_required
def community_emails():
    filter_status = request.args.get('filter', 'all')

    query = CommunityEmail.query.order_by(CommunityEmail.created_at.desc())
    emails = query.all()

    # Process blocking status manually since it's a join on string email
    # Or cleaner: Fetch all blocked emails first
    blocked_emails = [b.email for b in BlockedUser.query.filter(BlockedUser.email != None).all()]

    results = []
    for e in emails:
        is_blocked = e.email in blocked_emails
        if filter_status == 'blocked' and not is_blocked:
            continue
        if filter_status == 'active' and is_blocked:
            continue

        results.append({
            'id': e.id,
            'email': e.email,
            'created_at': e.created_at,
            'agreed_to_terms': e.agreed_to_terms,
            'is_blocked': is_blocked
        })

    return render_template('admin_emails.html', emails=results, filter=filter_status)

@admin_bp.route('/unhide_entry/<int:entry_id>', methods=['POST'])
@login_required
def unhide_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    entry.is_hidden = False
    entry.flag_count = 0  # Reset flags on approval
    db.session.commit()
    flash(_('Entry approved and reposted.'))
    return redirect(url_for('admin.flagged_entries'))

@admin_bp.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    # This route might receive user_id=0 or null if it was anonymous, but URL requires int.
    # The template should pass a valid user ID if registered, or we need a way to block by Entry ID to get the email.
    # Current template logic passes user_id from entry.user_id. If entry.user_id is None (anonymous), this route might fail or needs adjustment.
    # Let's adjust to finding the entry first if we want to block the *author* of an entry, regardless of registration.
    # But standard route is /block_user/ID.
    # Let's create a route that takes Entry ID to handle both cases better.

    user = User.query.get(user_id)
    if user:
        # Block registered user
        if not BlockedUser.query.filter_by(user_id=user.id).first():
            blocked = BlockedUser(user_id=user.id, email=user.email, reason="Blocked by admin")
            db.session.add(blocked)
            db.session.commit()
            flash(_('User %(username)s blocked.', username=user.username))
    return redirect(url_for('admin.flagged_entries'))

@admin_bp.route('/block_author/<int:entry_id>', methods=['POST'])
@login_required
def block_author(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)

    if entry.user_id:
        # Registered User
        if not BlockedUser.query.filter_by(user_id=entry.user_id).first():
            user = User.query.get(entry.user_id)
            blocked = BlockedUser(user_id=entry.user_id, email=user.email, reason="Blocked by admin")
            db.session.add(blocked)
            db.session.commit()
            flash(_('Registered author blocked.'))
    elif entry.community_email_id:
        # Anonymous User via Email
        comm_email = CommunityEmail.query.get(entry.community_email_id)
        if comm_email and not BlockedUser.query.filter_by(email=comm_email.email).first():
            blocked = BlockedUser(email=comm_email.email, reason="Blocked by admin")
            db.session.add(blocked)
            db.session.commit()
            flash(_('Anonymous author (%(email)s) blocked.', email=comm_email.email))

    return redirect(url_for('admin.flagged_entries'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Note: Cascading deletes should be handled by DB or model configuration.
    # For now, we assume simple delete is sufficient or orphaned records remain as anonymous.
    db.session.delete(user)
    db.session.commit()
    flash(_('User deleted.'))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/unblock_user/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    blocked = BlockedUser.query.filter_by(user_id=user.id).first()
    if blocked:
        db.session.delete(blocked)
        db.session.commit()
        flash(_('User %(username)s unblocked.', username=user.username))
    else:
        flash(_('User is not blocked.'))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/unblock_email', methods=['POST'])
@login_required
def unblock_email():
    email = request.form.get('email')
    if email:
        blocked = BlockedUser.query.filter_by(email=email).first()
        if blocked:
            db.session.delete(blocked)
            db.session.commit()
            flash(_('Email %(email)s unblocked.', email=email))
        else:
            flash(_('Email is not blocked.'))
    return redirect(url_for('admin.community_emails'))

@admin_bp.route('/delete_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = PrayerEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash(_('Entry deleted.'))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/invite', methods=['POST'])
@login_required
def create_invite():
    code = str(uuid.uuid4())
    invite = AdminInvite(code=code, created_by_admin_id=current_user.id)
    db.session.add(invite)
    db.session.commit()
    flash(_('Invite code created: %(code)s', code=code))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/announcements', methods=['POST'])
@login_required
def create_announcement():
    message = request.form.get('message')
    if message:
        # Deactivate all previous announcements (optional rule: only one active)
        Announcement.query.update({Announcement.is_active: False})

        announcement = Announcement(message=message, created_by_admin_id=current_user.id)
        db.session.add(announcement)
        db.session.commit()
        flash(_('Announcement posted.'))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/announcements/deactivate', methods=['POST'])
@login_required
def deactivate_announcement():
    Announcement.query.update({Announcement.is_active: False})
    db.session.commit()
    flash(_('Announcement cleared.'))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/export_all_entries')
@login_required
def export_all_entries():
    # Export all public entries to CSV
    import csv
    from io import StringIO
    from flask import make_response

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'User', 'Content', 'Date', 'Category'])

    entries = PrayerEntry.query.order_by(PrayerEntry.created_at.desc()).all()
    for entry in entries:
        username = entry.author.username if entry.author else 'Anonymous'
        cw.writerow([entry.id, username, entry.content, entry.created_at, entry.category])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=all_prayers.csv"
    output.headers["Content-type"] = "text/csv"
    return output
@admin_bp.route('/system_health')
@login_required
def system_health():
    if not current_user.get_id().startswith('admin_'):
        return redirect(url_for('admin_auth.login'))

    import psutil

    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # DB Check
    db_status = 'Unknown'
    try:
        db.session.execute(func.now())
        db_status = 'Connected'
    except Exception as e:
        db_status = f'Error: {e}'

    stats = {
        'cpu': cpu_usage,
        'memory': memory.percent,
        'disk': disk.percent,
        'db_status': db_status
    }

    return render_template('admin_system_health.html', stats=stats)
from models import AdminUserNote

@admin_bp.route('/user/<int:user_id>/note', methods=['POST'])
@login_required
def add_user_note(user_id):
    content = request.form.get('content')
    if content:
        note = AdminUserNote(
            admin_id=current_user.id,
            user_id=user_id,
            content=content
        )
        db.session.add(note)
        db.session.commit()
        flash(_('Note added.'))
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/feedback')
@login_required
def feedback():
    items = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template('admin_feedback.html', items=items)

@admin_bp.route('/feedback/<int:feedback_id>/status', methods=['POST'])
@login_required
def update_feedback_status(feedback_id):
    item = Feedback.query.get_or_404(feedback_id)
    new_status = request.form.get('status')
    if new_status in ['new', 'read', 'in_progress', 'resolved']:
        item.status = new_status
        db.session.commit()
        flash(_('Status updated.'))
    return redirect(url_for('admin.feedback'))
