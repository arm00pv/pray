import unittest
from app import create_app, db
from models import User, Feedback, PrayerEntry

class NewFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_feedback_model(self):
        with self.app.app_context():
            f = Feedback(content="Test feedback", category="bug")
            db.session.add(f)
            db.session.commit()

            saved = Feedback.query.first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.content, "Test feedback")
            self.assertEqual(saved.category, "bug")
            self.assertEqual(saved.status, "new")

    def test_user_notification_pref(self):
        with self.app.app_context():
            u = User(username="test", email="test@test.com", password_hash="hash")
            db.session.add(u)
            db.session.commit()

            saved = User.query.first()
            self.assertTrue(saved.allow_email_notifications) # Default True

            saved.allow_email_notifications = False
            db.session.commit()

            self.assertFalse(User.query.first().allow_email_notifications)

if __name__ == '__main__':
    unittest.main()
