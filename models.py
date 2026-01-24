from flask_login import UserMixin
from datetime import datetime, timezone
from extensions import db

# Association Table for Many-to-Many relationship between PrayerEntry and Tag
entry_tags = db.Table('entry_tags',
    db.Column('entry_id', db.Integer, db.ForeignKey('prayer_entry.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True) # Added email
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    entries = db.relationship('PrayerEntry', backref='author', lazy=True)

    def get_id(self):
        return f"user_{self.id}"

class BlockedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    geolocation_data = db.Column(db.Text) # Storing as JSON string
    status = db.Column(db.String(20), default='active') # active, fulfilled, dropped
    is_continuous = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False) # Added is_public
    is_anonymous = db.Column(db.Boolean, default=False)
    flag_count = db.Column(db.Integer, default=0)
    stickers = db.Column(db.String(200)) # Comma separated list
    tags = db.relationship('Tag', secondary=entry_tags, lazy='subquery',
        backref=db.backref('entries', lazy=True))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0)
