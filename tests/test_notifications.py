import unittest
from app import create_app, db
from models import User, PushSubscription

class NotificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
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

    def test_subscribe(self):
        self.login()

        data = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/123',
            'keys': {
                'p256dh': 'key1',
                'auth': 'secret'
            }
        }

        resp = self.client.post('/notifications/subscribe', json=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['status'], 'success')

        with self.app.app_context():
            sub = PushSubscription.query.first()
            self.assertIsNotNone(sub)
            self.assertEqual(sub.endpoint, data['endpoint'])
            self.assertEqual(sub.user_id, 1)

    def test_duplicate_subscribe(self):
        self.test_subscribe() # First time

        data = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/123',
            'keys': {'p256dh': 'k', 'auth': 's'}
        }
        resp = self.client.post('/notifications/subscribe', json=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['message'], 'Already subscribed')

if __name__ == '__main__':
    unittest.main()
