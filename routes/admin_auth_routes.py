from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import Admin, AdminInvite
from extensions import db, bcrypt

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

@admin_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        invite_code = request.form.get('invite_code')

        invite = AdminInvite.query.filter_by(code=invite_code, is_used=False).first()
        if not invite:
            flash('Invalid or used invite code.')
            return redirect(url_for('admin_auth.register'))

        if Admin.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('admin_auth.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = Admin(username=username, password_hash=hashed_pw)
        invite.is_used = True

        db.session.add(admin)
        db.session.commit()

        login_user(admin)
        return redirect(url_for('admin.dashboard'))
    return render_template('admin_register.html')
