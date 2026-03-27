from models import Badge, UserBadge, User, PrayerEntry, Amen
from extensions import db

def seed_badges():
    """Seeds default badges if they don't exist."""
    badges = [
        # Entry Milestones
        {"name": "First Prayer", "description": "Shared your first prayer", "icon": "🙏", "criteria_type": "entries_count", "threshold": 1},
        {"name": "Prayer Warrior", "description": "Shared 10 prayers", "icon": "⚔️", "criteria_type": "entries_count", "threshold": 10},
        {"name": "Faithful", "description": "Shared 50 prayers", "icon": "🕊️", "criteria_type": "entries_count", "threshold": 50},

        # Streak Milestones
        {"name": "Dedicated", "description": "3-day prayer streak", "icon": "🔥", "criteria_type": "streak", "threshold": 3},
        {"name": "Unstoppable", "description": "7-day prayer streak", "icon": "⚡", "criteria_type": "streak", "threshold": 7},
        {"name": "Devoted", "description": "30-day prayer streak", "icon": "🌟", "criteria_type": "streak", "threshold": 30},

        # Amen Milestones
        {"name": "Encourager", "description": "Prayed for 5 others", "icon": "❤️", "criteria_type": "amens_count", "threshold": 5},
        {"name": "Community Pillar", "description": "Prayed for 20 others", "icon": "🏛️", "criteria_type": "amens_count", "threshold": 20}
    ]

    for b_data in badges:
        if not Badge.query.filter_by(name=b_data["name"]).first():
            badge = Badge(**b_data)
            db.session.add(badge)
    db.session.commit()

def check_and_award_badges(user):
    """Checks criteria and awards new badges to the user."""
    if not user:
        return []

    newly_earned = []

    # 1. Fetch all badges
    all_badges = Badge.query.all()

    # 2. Get user's current metrics
    entries_count = PrayerEntry.query.filter_by(user_id=user.id).count()
    amens_count = Amen.query.filter_by(user_id=user.id).count()
    streak = user.calculate_streak()

    metrics = {
        'entries_count': entries_count,
        'amens_count': amens_count,
        'streak': streak
    }

    # 3. Check each badge
    for badge in all_badges:
        # Check if already earned
        if UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
            continue

        # Check criteria
        metric_val = metrics.get(badge.criteria_type, 0)

        if metric_val >= badge.threshold:
            # Award!
            ub = UserBadge(user_id=user.id, badge_id=badge.id)
            db.session.add(ub)
            newly_earned.append(badge)

    if newly_earned:
        db.session.commit()

    return newly_earned
