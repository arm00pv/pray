from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from flask_babel import _

donation_bp = Blueprint('donation', __name__, url_prefix='/donate')

@donation_bp.route('/')
def index():
    return render_template('donate.html')

@donation_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Mock checkout flow
    amount = request.args.get('amount', 500)
    recurring = request.args.get('recurring')

    # Simulate processing delay or API call

    if recurring:
        flash(_('Thank you for becoming a monthly supporter!'))
    else:
        flash(_('Thank you for your donation!'))

    return redirect(url_for('entry.user_dashboard'))
