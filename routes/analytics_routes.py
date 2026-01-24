from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import PrayerEntry, Tag
from extensions import db

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def index():
    # Get user's entries
    entries = current_user.entries

    # Calculate tag frequency for this user
    tag_counts = {}
    for entry in entries:
        for tag in entry.tags:
            tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

    # Sort by count
    sorted_tags = sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)

    labels = [item[0] for item in sorted_tags[:10]] # Top 10
    data = [item[1] for item in sorted_tags[:10]]

    # Calculate category distribution
    category_counts = {}
    for entry in entries:
        cat = entry.category or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    cat_labels = list(category_counts.keys())
    cat_data = list(category_counts.values())

    return render_template('analytics.html', labels=labels, data=data, cat_labels=cat_labels, cat_data=cat_data)
