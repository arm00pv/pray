import unittest
from app import create_app, db
from models import User, PrayerEntry, Amen, Badge, UserBadge
from utils.gamification import seed_badges, check_and_award_badges
from flask_bcrypt import Bcrypt

class GamificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.bcrypt = Bcrypt(self.app)

        with self.app.app_context():
            db.create_all()
            seed_badges()

            hashed_pw = self.bcrypt.generate_password_hash('password').decode('utf-8')
            self.user = User(username='testuser', email='test@test.com', password_hash=hashed_pw)
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_badge_seeding(self):
        with self.app.app_context():
            badges = Badge.query.all()
            self.assertTrue(len(badges) >= 5)
            self.assertIsNotNone(Badge.query.filter_by(name="First Prayer").first())

    def test_award_first_prayer_badge(self):
        with self.app.app_context():
            user = User.query.first()

            # Post 1 entry
            entry = PrayerEntry(user_id=user.id, content="My first prayer")
            db.session.add(entry)
            db.session.commit()

            # Check badges
            new_badges = check_and_award_badges(user)
            self.assertEqual(len(new_badges), 1)
            self.assertEqual(new_badges[0].name, "First Prayer")

            # Check DB persistence
            user_badges = UserBadge.query.filter_by(user_id=user.id).all()
            self.assertEqual(len(user_badges), 1)

    def test_award_encourager_badge(self):
         with self.app.app_context():
            user = User.query.first()

            # Create dummy entry by someone else
            other = User(username='other', password_hash='hash')
            db.session.add(other)
            db.session.commit()

            entry = PrayerEntry(user_id=other.id, content="Help me")
            db.session.add(entry)
            db.session.commit()

            # Add 5 amens (simulate 5 different entries for logic, or same? Logic just counts Total Amens)
            # gamification.py: amens_count = Amen.query.filter_by(user_id=user.id).count()
            # So duplicate amens on same entry might count if DB allows unique violation?
            # Model: Amen(user_id, entry_id). Usually we prevent duplicates in route.
            # But let's create 5 entries to be safe.

            for i in range(5):
                 e = PrayerEntry(user_id=other.id, content=f"Prayer {i}")
                 db.session.add(e)
                 db.session.commit()
                 amen = Amen(user_id=user.id, entry_id=e.id)
                 db.session.add(amen)

            db.session.commit()

            new_badges = check_and_award_badges(user)
            # Should earn "Encourager" (threshold 5)
            # Note: "First Prayer" is not earned here.

            earned_names = [b.name for b in new_badges]
            self.assertIn("Encourager", earned_names)

if __name__ == '__main__':
    unittest.main()
