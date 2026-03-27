import unittest
from app import create_app, db
from models import User, PrayerGroup, GroupPoll, GroupPollOption, GroupPollVote

class PollsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create user & admin
            u = User(username='user', email='user@test.com', password_hash='hash')
            admin = User(username='admin', email='admin@test.com', password_hash='hash')
            db.session.add_all([u, admin])
            db.session.commit()

            # Create group
            group = PrayerGroup(name='Test Group', created_by=admin.id)
            group.members.append(admin)
            group.members.append(u)
            group.admins.append(admin)
            db.session.add(group)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username):
        with self.client.session_transaction() as sess:
            # We need to find the user ID.
            # In unit tests with :memory:, IDs are usually 1, 2...
            # user=1, admin=2
            sess['_user_id'] = 'user_2' if username == 'admin' else 'user_1'

    def test_create_poll(self):
        self.login('admin')
        resp = self.client.post('/groups/1/polls/create', data={
            'question': 'What to pray for?',
            'options': 'Health, Peace, Joy'
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Poll created', resp.data)

        with self.app.app_context():
            poll = GroupPoll.query.first()
            self.assertIsNotNone(poll)
            self.assertEqual(poll.question, 'What to pray for?')
            self.assertEqual(len(poll.options), 3)

    def test_vote_poll(self):
        self.test_create_poll() # Create it first

        # User votes
        self.login('user')
        with self.app.app_context():
            poll = GroupPoll.query.first()
            option = poll.options[0]
            poll_id = poll.id
            option_id = option.id

        resp = self.client.post(f'/groups/polls/{poll_id}/vote', data={
            'option_id': option_id
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Vote recorded', resp.data)

        with self.app.app_context():
            vote = GroupPollVote.query.first()
            self.assertIsNotNone(vote)
            self.assertEqual(vote.user_id, 1)

if __name__ == '__main__':
    unittest.main()
