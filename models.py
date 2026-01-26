from flask_login import UserMixin
from datetime import datetime, timezone
from extensions import db

# Association Table for Many-to-Many relationship between PrayerEntry and Tag
entry_tags = db.Table('entry_tags',
    db.Column('entry_id', db.Integer, db.ForeignKey('prayer_entry.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class CommunityEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    agreed_to_terms = db.Column(db.Boolean, default=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True) # Added email
    about_me = db.Column(db.String(500), nullable=True) # Added Bio
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    security_question = db.Column(db.String(255), nullable=True)
    security_answer_hash = db.Column(db.String(255), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    entries = db.relationship('PrayerEntry', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def get_id(self):
        return f"user_{self.id}"

    def calculate_streak(self):
        """Calculates consecutive days with at least one prayer entry."""
        if not self.entries:
            return 0

        # Get unique dates of entries, sorted descending
        dates = sorted(list(set(e.created_at.date() for e in self.entries)), reverse=True)

        if not dates:
            return 0

        today = datetime.now(timezone.utc).date()

        # Check if the most recent entry is today or yesterday
        # If the last entry was before yesterday, streak is broken (0), unless we count the streak up to that point?
        # Typically "current streak" means active. If I didn't pray today (yet) but prayed yesterday, is my streak 1 or 0?
        # Usually, if I prayed yesterday, my streak is alive. If I miss yesterday, it resets.

        if (today - dates[0]).days > 1:
            return 0

        streak = 1
        for i in range(len(dates) - 1):
            if (dates[i] - dates[i+1]).days == 1:
                streak += 1
            else:
                break
        return streak

class BlockedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=True) # Nullable if blocking by ID only
    user_id = db.Column(db.Integer, nullable=True) # Block by ID
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    security_question = db.Column(db.String(255), nullable=True)
    security_answer_hash = db.Column(db.String(255), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def get_id(self):
        return f"admin_{self.id}"

class AdminInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class PrayerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Changed to nullable
    community_email_id = db.Column(db.Integer, db.ForeignKey('community_email.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    geolocation_data = db.Column(db.Text) # Storing as JSON string
    status = db.Column(db.String(20), default='active') # active, fulfilled, dropped
    is_continuous = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False) # Added is_public
    is_anonymous = db.Column(db.Boolean, default=False)
    flag_count = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), nullable=True)
    is_private = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    stickers = db.Column(db.String(200)) # Comma separated list
    tags = db.relationship('Tag', secondary=entry_tags, lazy='subquery',
        backref=db.backref('entries', lazy=True))
    amens = db.relationship('Amen', backref='entry', lazy=True)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0)

class Amen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('prayer_entry.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class GratitudeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Testimony(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author = db.relationship('User', backref='testimonies', lazy=True)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('prayer_group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    author = db.relationship('User')

group_members = db.Table('group_members',
    db.Column('group_id', db.Integer, db.ForeignKey('prayer_group.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

group_admins = db.Table('group_admins',
    db.Column('group_id', db.Integer, db.ForeignKey('prayer_group.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class PrayerGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    members = db.relationship('User', secondary=group_members, lazy='subquery',
        backref=db.backref('prayer_groups', lazy=True))
    admins = db.relationship('User', secondary=group_admins, lazy='subquery',
        backref=db.backref('admin_groups', lazy=True))
    messages = db.relationship('GroupMessage', backref='group', lazy=True)
