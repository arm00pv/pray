from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user, logout_user
from flask_babel import _
from models import (
    User, Amen, Praise, GroupMessage, PrivateMessage, PrayerReminder,
    SavedPrayer, SpiritualGoal, Notification, GratitudeEntry,
    AdminUserNote, PrayerPartnerMatch, Testimony, PrayerEntry,
    GroupEvent, PrayerGroup, SermonNote, ReadingProgress
)
from extensions import db, bcrypt
import json
from datetime import datetime
import io

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            email = request.form.get('email')
            about_me = request.form.get('about_me')
            profile_image_url = request.form.get('profile_image_url')
            preferred_language = request.form.get('preferred_language')
            allow_email_notifications = 'allow_email_notifications' in request.form

            # Check uniqueness if changed
            if email != current_user.email:
                if User.query.filter_by(email=email).first():
                    flash(_('Email already in use.'))
                    return redirect(url_for('settings.index'))
                current_user.email = email

            current_user.about_me = about_me
            current_user.profile_image_url = profile_image_url
            current_user.allow_email_notifications = allow_email_notifications

            if preferred_language in ['en', 'es']:
                current_user.preferred_language = preferred_language

            db.session.commit()
            flash(_('Profile updated.'))

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')

            if not bcrypt.check_password_hash(current_user.password_hash, current_password):
                flash(_('Incorrect current password.'))
            else:
                current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                flash(_('Password changed.'))

        return redirect(url_for('settings.index'))

    return render_template('settings.html')

@settings_bp.route('/export', methods=['GET'])
@login_required
def export_all_data():
    data = {
        'version': 1,
        'exported_at': datetime.utcnow().isoformat(),
        'user': {
            'username': current_user.username,
            'email': current_user.email,
            'about_me': current_user.about_me,
            'preferred_language': current_user.preferred_language
        },
        'prayers': [],
        'sermons': [],
        'gratitude': [],
        'reading_progress': []
    }

    # Prayers
    prayers = PrayerEntry.query.filter_by(user_id=current_user.id).all()
    for p in prayers:
        data['prayers'].append({
            'content': p.content,
            'created_at': p.created_at.isoformat(),
            'status': p.status,
            'category': p.category,
            'is_private': p.is_private,
            'is_public': p.is_public,
            'mood': p.mood,
            'reflection': p.reflection
        })

    # Sermons
    sermons = SermonNote.query.filter_by(user_id=current_user.id).all()
    for s in sermons:
        data['sermons'].append({
            'title': s.title,
            'preacher': s.preacher,
            'scripture': s.scripture_reference,
            'content': s.content,
            'created_at': s.created_at.isoformat()
        })

    # Gratitude
    gratitude = GratitudeEntry.query.filter_by(user_id=current_user.id).all()
    for g in gratitude:
        data['gratitude'].append({
            'content': g.content,
            'created_at': g.created_at.isoformat()
        })

    # Reading
    reading = ReadingProgress.query.filter_by(user_id=current_user.id).all()
    for r in reading:
        data['reading_progress'].append({
            'plan_day': r.plan_day,
            'reading_date': r.reading_date.isoformat(),
            'is_completed': r.is_completed
        })

    response = make_response(json.dumps(data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    filename = f"backup_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.json"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@settings_bp.route('/import', methods=['POST'])
@login_required
def import_data():
    file = request.files.get('backup_file')
    if not file:
        flash(_('No file selected.'))
        return redirect(url_for('settings.index'))

    try:
        data = json.load(file)

        # Simple stats
        stats = {'prayers': 0, 'sermons': 0, 'gratitude': 0}

        # Import Prayers
        if 'prayers' in data:
            for p_data in data['prayers']:
                # Avoid exact duplicates based on content and approximate time?
                # For simplicity in this demo, we just add everything as new entries
                # but let's check content to avoid obvious spamming the same backup
                exists = PrayerEntry.query.filter_by(user_id=current_user.id, content=p_data['content']).first()
                if not exists:
                    entry = PrayerEntry(
                        user_id=current_user.id,
                        content=p_data['content'],
                        status=p_data.get('status', 'active'),
                        category=p_data.get('category'),
                        is_private=p_data.get('is_private', True),
                        is_public=p_data.get('is_public', False),
                        mood=p_data.get('mood'),
                        reflection=p_data.get('reflection'),
                        created_at=datetime.fromisoformat(p_data['created_at']) if 'created_at' in p_data else datetime.utcnow()
                    )
                    db.session.add(entry)
                    stats['prayers'] += 1

        # Import Sermons
        if 'sermons' in data:
            for s_data in data['sermons']:
                exists = SermonNote.query.filter_by(user_id=current_user.id, title=s_data['title'], content=s_data['content']).first()
                if not exists:
                    note = SermonNote(
                        user_id=current_user.id,
                        title=s_data['title'],
                        preacher=s_data.get('preacher'),
                        scripture_reference=s_data.get('scripture'),
                        content=s_data['content'],
                        created_at=datetime.fromisoformat(s_data['created_at']) if 'created_at' in s_data else datetime.utcnow()
                    )
                    db.session.add(note)
                    stats['sermons'] += 1

        # Import Gratitude
        if 'gratitude' in data:
            for g_data in data['gratitude']:
                exists = GratitudeEntry.query.filter_by(user_id=current_user.id, content=g_data['content']).first()
                if not exists:
                    entry = GratitudeEntry(
                        user_id=current_user.id,
                        content=g_data['content'],
                        created_at=datetime.fromisoformat(g_data['created_at']) if 'created_at' in g_data else datetime.utcnow()
                    )
                    db.session.add(entry)
                    stats['gratitude'] += 1

        # Import Reading (Optional, maybe overwrite or merge)
        if 'reading_progress' in data:
            for r_data in data['reading_progress']:
                if 'plan_day' in r_data and r_data['plan_day']:
                    exists = ReadingProgress.query.filter_by(user_id=current_user.id, plan_day=r_data['plan_day']).first()
                    if not exists:
                        rp = ReadingProgress(
                            user_id=current_user.id,
                            plan_day=r_data['plan_day'],
                            reading_date=datetime.fromisoformat(r_data['reading_date']).date(),
                            is_completed=r_data.get('is_completed', True)
                        )
                        db.session.add(rp)

        db.session.commit()
        flash(_('Import successful: %(p)d prayers, %(s)d sermons, %(g)d gratitude entries added.', p=stats['prayers'], s=stats['sermons'], g=stats['gratitude']))

    except json.JSONDecodeError:
        flash(_('Invalid JSON file.'))
    except Exception as e:
        db.session.rollback()
        flash(_('Error importing data: %(error)s', error=str(e)))

    return redirect(url_for('settings.index'))

@settings_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user
    uid = user.id

    try:
        # 1. Delete direct dependencies (where User is the dependent)
        Amen.query.filter_by(user_id=uid).delete()
        Praise.query.filter_by(user_id=uid).delete()
        GroupMessage.query.filter_by(user_id=uid).delete()
        PrivateMessage.query.filter((PrivateMessage.sender_id==uid) | (PrivateMessage.recipient_id==uid)).delete()
        PrayerReminder.query.filter_by(user_id=uid).delete()
        SavedPrayer.query.filter_by(user_id=uid).delete()
        SpiritualGoal.query.filter_by(user_id=uid).delete()
        Notification.query.filter_by(user_id=uid).delete()
        GratitudeEntry.query.filter_by(user_id=uid).delete()
        AdminUserNote.query.filter_by(user_id=uid).delete()
        PrayerPartnerMatch.query.filter((PrayerPartnerMatch.user_id_1==uid) | (PrayerPartnerMatch.user_id_2==uid)).delete()

        # 2. Delete Testimonies and their Praises
        user_testimonies = Testimony.query.filter_by(user_id=uid).all()
        for t in user_testimonies:
            Praise.query.filter_by(testimony_id=t.id).delete()
            db.session.delete(t)

        # 3. Delete Prayer Entries and their dependencies
        user_entries = PrayerEntry.query.filter_by(user_id=uid).all()
        for e in user_entries:
            Amen.query.filter_by(entry_id=e.id).delete()
            SavedPrayer.query.filter_by(prayer_entry_id=e.id).delete()
            PrayerReminder.query.filter_by(entry_id=e.id).delete()
            db.session.delete(e)

        # 4. Handle Groups
        # Remove user from memberships and admin roles
        user.prayer_groups = []
        user.admin_groups = []

        # Delete events created by the user (regardless of group)
        GroupEvent.query.filter_by(created_by=uid).delete()

        # Delete groups created by the user
        owned_groups = PrayerGroup.query.filter_by(created_by=uid).all()
        for g in owned_groups:
             GroupMessage.query.filter_by(group_id=g.id).delete()
             GroupEvent.query.filter_by(group_id=g.id).delete()
             # Clear associations
             g.members = []
             g.admins = []
             db.session.delete(g)

        # 5. Delete the User
        db.session.delete(user)
        db.session.commit()

        logout_user()
        flash(_('Your account has been permanently deleted.'), 'success')
        return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        flash(_('An error occurred while deleting your account: %(error)s', error=str(e)), 'danger')
        return redirect(url_for('settings.index'))
