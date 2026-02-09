import unittest
import json
import io
from app import create_app, db
from models import User, PrayerEntry, SermonNote

class ImportExportTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # User 1
            u = User(username='test', email='test@test.com', password_hash='hash')
            db.session.add(u)
            db.session.commit()

            # Add data
            p = PrayerEntry(user_id=1, content="Export Test Prayer", status="active")
            s = SermonNote(user_id=1, title="Export Sermon", content="Sermon Content")
            db.session.add_all([p, s])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = 'user_1'

    def test_export(self):
        self.login()
        resp = self.client.get('/settings/export')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')

        data = json.loads(resp.data)
        self.assertEqual(data['user']['username'], 'test')
        self.assertEqual(len(data['prayers']), 1)
        self.assertEqual(data['prayers'][0]['content'], "Export Test Prayer")
        self.assertEqual(len(data['sermons']), 1)

    def test_import(self):
        self.login()
        # Prepare JSON file
        import_data = {
            'prayers': [{'content': 'Imported Prayer', 'status': 'active'}],
            'sermons': [{'title': 'Imported Sermon', 'content': 'Content'}]
        }
        json_bytes = json.dumps(import_data).encode('utf-8')
        file_storage = (io.BytesIO(json_bytes), 'backup.json')

        resp = self.client.post('/settings/import', data={
            'backup_file': file_storage
        }, follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Import successful', resp.data)

        with self.app.app_context():
            # Check for new entries
            # Should have 2 prayers now (1 original, 1 imported)
            count = PrayerEntry.query.count()
            self.assertEqual(count, 2)

            new_entry = PrayerEntry.query.filter_by(content='Imported Prayer').first()
            self.assertIsNotNone(new_entry)

if __name__ == '__main__':
    unittest.main()
