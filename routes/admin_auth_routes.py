from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import Admin, AdminInvite
from extensions import db, bcrypt
from utils import validate_password_strength
import uuid
from datetime import datetime, timedelta

admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admins')

@admin_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and bcrypt.check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid admin credentials')
    return render_template('admin_login.html')

@admin_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        admin = Admin.query.filter_by(username=username).first()
        if admin:
            return render_template('answer_security_question.html', user_id=admin.id, question=admin.security_question, is_admin=True)
        else:
            flash('Admin username not found.')
    return render_template('forgot_password.html', is_admin=True)

@admin_auth_bp.route('/verify-security-answer/<int:admin_id>', methods=['POST'])
def verify_security_answer(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    answer = request.form.get('security_answer')

    if answer and admin.security_answer_hash and bcrypt.check_password_hash(admin.security_answer_hash, answer.lower().strip()):
        token = str(uuid.uuid4())
        admin.reset_token = token
        admin.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return redirect(url_for('admin_auth.reset_password', token=token))
    else:
        flash('Incorrect security answer.')
        return render_template('answer_security_question.html', user_id=admin.id, question=admin.security_question, is_admin=True)

@admin_auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    admin = Admin.query.filter_by(reset_token=token).first()
    if not admin or not admin.reset_token_expiry or admin.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link.')
        return redirect(url_for('admin_auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('reset_password.html', token=token, is_admin=True)

        valid, errors = validate_password_strength(password)
        if not valid:
            for error in errors:
                flash(error)
            return render_template('reset_password.html', token=token, is_admin=True)

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        admin.password_hash = hashed_pw
        admin.reset_token = None
        admin.reset_token_expiry = None
        db.session.commit()
        flash('Password updated successfully. Please login.')
        return redirect(url_for('admin_auth.login'))

    return render_template('reset_password.html', token=token, is_admin=True)

@admin_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        invite_code = request.form.get('invite_code')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        invite = AdminInvite.query.filter_by(code=invite_code, is_used=False).first()
        if not invite:
            flash('Invalid or used invite code.')
            return redirect(url_for('admin_auth.register'))

        if Admin.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('admin_auth.register'))

        valid, errors = validate_password_strength(password)
        if not valid:
            for error in errors:
                flash(error)
            return redirect(url_for('admin_auth.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        hashed_answer = bcrypt.generate_password_hash(security_answer.lower().strip()).decode('utf-8') if security_answer else None

        admin = Admin(
            username=username,
            email=email,
            password_hash=hashed_pw,
            security_question=security_question,
            security_answer_hash=hashed_answer
        )
        invite.is_used = True

        db.session.add(admin)
        db.session.commit()

        login_user(admin)
        return redirect(url_for('admin.dashboard'))
    return render_template('admin_register.html')
