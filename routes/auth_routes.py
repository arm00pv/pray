from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from models import User, Admin, BlockedUser
from extensions import db, bcrypt, login_manager
from utils import send_email, validate_password_strength
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

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

        # Convert empty string email to None to avoid unique constraint violation on ''
        if not email or email.strip() == '':
            email = None

        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        if not username or not password or not security_question or not security_answer:
            flash('All fields including security question/answer are required.')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.register'))

        valid, errors = validate_password_strength(password)
        if not valid:
            for error in errors:
                flash(error)
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))

        if email and User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('auth.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        hashed_answer = bcrypt.generate_password_hash(security_answer.lower().strip()).decode('utf-8')
        token = str(uuid.uuid4())

        # Get preferred language from session or default to 'en'
        preferred_language = session.get('language', 'en')

        user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            verification_token=token,
            is_verified=False,
            security_question=security_question,
            security_answer_hash=hashed_answer,
            preferred_language=preferred_language
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Username or Email already exists.')
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.')
            print(f"Registration error: {e}")
            return redirect(url_for('auth.register'))

        if email:
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            send_email(email, "Verify your email", f"Please verify your email by clicking: {verify_url}")

        login_user(user)
        flash('Registration successful. Please check your email to verify your account.')
        return redirect(url_for('entry.user_dashboard'))
    return render_template('register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('answer_security_question.html', user_id=user.id, question=user.security_question)
        else:
            flash('Username not found.')
    return render_template('forgot_password.html')

@auth_bp.route('/verify-security-answer/<int:user_id>', methods=['POST'])
def verify_security_answer(user_id):
    user = User.query.get_or_404(user_id)
    answer = request.form.get('security_answer')

    if answer and bcrypt.check_password_hash(user.security_answer_hash, answer.lower().strip()):
        # Step 2 passed. Generate reset token.
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # Allow direct reset since email is optional
        return redirect(url_for('auth.reset_password', token=token))
    else:
        flash('Incorrect security answer.')
        return render_template('answer_security_question.html', user_id=user.id, question=user.security_question)

    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('reset_password.html', token=token)

        valid, errors = validate_password_strength(password)
        if not valid:
            for error in errors:
                flash(error)
            return render_template('reset_password.html', token=token)

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password_hash = hashed_pw
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        flash('Password updated successfully. Please login.')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)

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

# Social Login Disabled
@auth_bp.route('/login/<provider>')
def social_login(provider):
    flash('Social login is currently disabled.')
    return redirect(url_for('auth.login'))
