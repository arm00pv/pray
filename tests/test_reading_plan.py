import unittest
from app import create_app, db
from models import User, ReadingProgress

class ReadingPlanTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create test user
            u = User(username='test', email='test@test.com', password_hash='hash')
            db.session.add(u)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = 'user_1'

    def test_reading_plan_routes(self):
        self.login()
        # 1. Index
        resp = self.client.get('/reading/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Bible Reading Plan', resp.data)

        # 2. Mark Day 1
        resp = self.client.post('/reading/mark/1', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Day 1 marked as read', resp.data)

        # 3. Verify DB
        with self.app.app_context():
            prog = ReadingProgress.query.filter_by(user_id=1, plan_day=1).first()
            self.assertIsNotNone(prog)
            self.assertTrue(prog.is_completed)

        # 4. Toggle Off
        resp = self.client.post('/reading/mark/1', follow_redirects=True)
        self.assertIn(b'Day 1 marked as unread', resp.data)

if __name__ == '__main__':
    unittest.main()
