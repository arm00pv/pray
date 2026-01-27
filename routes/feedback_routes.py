from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user
from flask_babel import _
from models import Feedback
from extensions import db

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

@feedback_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form.get('category')
        content = request.form.get('content')
        # If logged in, use their email. If not, check form.
        email = request.form.get('email')

        if not content:
            flash(_('Please provide some content.'), 'danger')
            return redirect(url_for('feedback.index'))

        feedback = Feedback(
            category=category,
            content=content,
            email=email if not current_user.is_authenticated else current_user.email,
            user_id=current_user.id if current_user.is_authenticated else None
        )

        db.session.add(feedback)
        db.session.commit()

        flash(_('Thank you for your feedback!'), 'success')
        return redirect(url_for('index'))

    return render_template('feedback.html')
