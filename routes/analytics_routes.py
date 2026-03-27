from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import PrayerEntry, Tag
from extensions import db
from collections import defaultdict
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def index():
    # Get user's entries
    entries = current_user.entries

    # 1. Tag Frequency
    tag_counts = {}
    for entry in entries:
        for tag in entry.tags:
            tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

    sorted_tags = sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)
    labels = [item[0] for item in sorted_tags[:10]]
    data = [item[1] for item in sorted_tags[:10]]

    # 2. Category Distribution
    category_counts = {}
    for entry in entries:
        cat = entry.category or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    cat_labels = list(category_counts.keys())
    cat_data = list(category_counts.values())

    # 3. Mood Distribution
    mood_counts = {}
    for entry in entries:
        if entry.mood:
            mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1

    mood_labels = list(mood_counts.keys())
    mood_data = list(mood_counts.values())

    # 4. Activity Timeline (Last 30 Days)
    today = datetime.utcnow().date()
    timeline_counts = defaultdict(int)

    # Initialize last 30 days with 0
    date_labels = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        date_labels.append(d_str)
        timeline_counts[d_str] = 0

    for entry in entries:
        d_str = entry.created_at.strftime('%Y-%m-%d')
        if d_str in timeline_counts:
            timeline_counts[d_str] += 1

    timeline_data = [timeline_counts[d] for d in date_labels]

    return render_template('analytics.html',
                           labels=labels, data=data,
                           cat_labels=cat_labels, cat_data=cat_data,
                           mood_labels=mood_labels, mood_data=mood_data,
                           date_labels=date_labels, timeline_data=timeline_data)
