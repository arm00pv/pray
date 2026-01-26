import unittest
from app import create_app, db
from models import User, PrivateMessage, PrayerReminder, PrayerEntry
from datetime import datetime, timedelta, timezone

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_private_message(self):
        u1 = User(username='u1', password_hash='x', email='u1@test.com')
        u2 = User(username='u2', password_hash='x', email='u2@test.com')
        db.session.add_all([u1, u2])
        db.session.commit()

        msg = PrivateMessage(sender_id=u1.id, recipient_id=u2.id, content="Hello")
        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(u1.sent_messages), 1)
        self.assertEqual(len(u2.received_messages), 1)
        self.assertEqual(u2.received_messages[0].content, "Hello")

    def test_prayer_reminder(self):
        u1 = User(username='u1', password_hash='x', email='u1@test.com')
        db.session.add(u1)
        db.session.commit()

        entry = PrayerEntry(user_id=u1.id, content="Pray for test")
        db.session.add(entry)
        db.session.commit()

        future = datetime.now(timezone.utc) + timedelta(days=1)
        reminder = PrayerReminder(user_id=u1.id, entry_id=entry.id, reminder_datetime=future)
        db.session.add(reminder)
        db.session.commit()

        self.assertFalse(reminder.is_sent)
        self.assertEqual(reminder.entry.content, "Pray for test")

if __name__ == '__main__':
    unittest.main()
