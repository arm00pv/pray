from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from flask_babel import _
from models import (
    User, Amen, Praise, GroupMessage, PrivateMessage, PrayerReminder,
    SavedPrayer, SpiritualGoal, Notification, GratitudeEntry,
    AdminUserNote, PrayerPartnerMatch, Testimony, PrayerEntry,
    GroupEvent, PrayerGroup
)
from extensions import db, bcrypt

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
