from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import User, Admin, BlockedUser
from extensions import db, bcrypt, login_manager
from utils import send_email
import uuid

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('user_'):
        return User.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('admin_'):
        return Admin.query.get(int(user_id.split('_')[1]))
    return None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))

        if email and User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('auth.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        token = str(uuid.uuid4())
        user = User(username=username, email=email, password_hash=hashed_pw, verification_token=token, is_verified=False)
        db.session.add(user)
        db.session.commit()

        if email:
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            send_email(email, "Verify your email", f"Please verify your email by clicking: {verify_url}")

        login_user(user)
        flash('Registration successful. Please check your email to verify your account.')
        return redirect(url_for('entry.user_dashboard'))
    return render_template('register.html')

@auth_bp.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Email verified! You can now use all features.')
    else:
        flash('Invalid verification token.')
    return redirect(url_for('entry.user_dashboard'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            # Check if blocked
            if user.email:
                blocked = BlockedUser.query.filter_by(email=user.email).first()
                if blocked:
                    flash(f'Account blocked: {blocked.reason}')
                    return render_template('login.html')

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('entry.user_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
