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
    profile_image_url = db.Column(db.String(255), nullable=True) # Added Profile Image
    preferred_language = db.Column(db.String(10), default='en') # Added Preferred Language
    allow_email_notifications = db.Column(db.Boolean, default=True) # Notification Preference
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
    mood = db.Column(db.String(20), nullable=True) # Added Mood

    # Social Login
    oauth_provider = db.Column(db.String(20), nullable=True) # google, facebook
    oauth_id = db.Column(db.String(100), nullable=True)

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
    reflection = db.Column(db.Text, nullable=True) # Added Private Reflection
    mood = db.Column(db.String(20), nullable=True) # Added Mood to Entry
    is_urgent = db.Column(db.Boolean, default=False)
    urgent_expiry = db.Column(db.DateTime, nullable=True)
    tags = db.relationship('Tag', secondary=entry_tags, lazy='subquery',
        backref=db.backref('entries', lazy=True))
    amens = db.relationship('Amen', backref='entry', lazy=True)
    encouragements = db.relationship('Encouragement', backref='entry', lazy=True, cascade="all, delete-orphan")

class Encouragement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('prayer_entry.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='encouragements')

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

class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    keys_p256dh = db.Column(db.String(200), nullable=False)
    keys_auth = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='push_subscriptions')

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
    praises = db.relationship('Praise', backref='testimony', lazy=True)

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
    purpose = db.Column(db.Text, nullable=True) # Extended profile purpose
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    members = db.relationship('User', secondary=group_members, lazy='subquery',
        backref=db.backref('prayer_groups', lazy=True))
    admins = db.relationship('User', secondary=group_admins, lazy='subquery',
        backref=db.backref('admin_groups', lazy=True))
    messages = db.relationship('GroupMessage', backref='group', lazy=True)
    events = db.relationship('GroupEvent', backref='group', lazy=True)

class GroupEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('prayer_group.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    event_datetime = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)

class Praise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    testimony_id = db.Column(db.Integer, db.ForeignKey('testimony.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

class PrayerReminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('prayer_entry.id'), nullable=False)
    reminder_datetime = db.Column(db.DateTime, nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='reminders')
    entry = db.relationship('PrayerEntry')

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), default='INFO') # INFO, WARNING, ERROR
    message = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class SavedPrayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prayer_entry_id = db.Column(db.Integer, db.ForeignKey('prayer_entry.id'), nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='saved_prayers')
    prayer_entry = db.relationship('PrayerEntry')

class PrayerPartnerMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id_1 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id_2 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class SpiritualGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False) # 'prayer', 'reading', 'gratitude'
    target_count = db.Column(db.Integer, default=1)
    current_count = db.Column(db.Integer, default=0)
    week_start_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())

    user = db.relationship('User', backref='goals')

class AdminUserNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    admin = db.relationship('Admin')
    user = db.relationship('User', backref='admin_notes')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    category = db.Column(db.String(50), default='general') # bug, feature, general, prayer_request
    content = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(150), nullable=True) # For anonymous feedback
    status = db.Column(db.String(20), default='new') # new, read, in_progress, resolved
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='feedback_entries')

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50)) # Emoji or class name
    criteria_type = db.Column(db.String(50)) # e.g., 'entries_count', 'amens_count', 'streak'
    threshold = db.Column(db.Integer, default=1)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='badges')
    badge = db.relationship('Badge')

class ReadingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reading_date = db.Column(db.Date, nullable=False)
    plan_day = db.Column(db.Integer, nullable=True) # Day number 1-365
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='reading_progress')

class SermonNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    preacher = db.Column(db.String(100), nullable=True)
    scripture_reference = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='sermon_notes')

class GroupRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('prayer_group.id'), nullable=False)
    prayer_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='group_requests')
    group = db.relationship('PrayerGroup', backref='requests')

class GroupJoinRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('prayer_group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='join_requests')
    group = db.relationship('PrayerGroup', backref='join_requests')

class GroupPoll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('prayer_group.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    group = db.relationship('PrayerGroup', backref='polls')
    options = db.relationship('GroupPollOption', backref='poll', lazy=True, cascade="all, delete-orphan")
    votes = db.relationship('GroupPollVote', backref='poll', lazy=True, cascade="all, delete-orphan")

class GroupPollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('group_poll.id'), nullable=False)
    text = db.Column(db.String(100), nullable=False)
    votes = db.relationship('GroupPollVote', backref='option', lazy=True, cascade="all, delete-orphan")

class GroupPollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('group_poll.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('group_poll_option.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class UserBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class PrayerList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='prayer_lists')
    items = db.relationship('PrayerListItem', backref='list', lazy=True, cascade="all, delete-orphan")

class PrayerListItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('prayer_list.id'), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    is_answered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
