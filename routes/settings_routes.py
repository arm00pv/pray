from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User
from extensions import db, bcrypt

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            email = request.form.get('email')
            # Check uniqueness if changed
            if email != current_user.email:
                if User.query.filter_by(email=email).first():
                    flash('Email already in use.')
                    return redirect(url_for('settings.index'))
                current_user.email = email
                db.session.commit()
                flash('Profile updated.')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')

            if not bcrypt.check_password_hash(current_user.password_hash, current_password):
                flash('Incorrect current password.')
            else:
                current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
                db.session.commit()
                flash('Password changed.')

        return redirect(url_for('settings.index'))

    return render_template('settings.html')
