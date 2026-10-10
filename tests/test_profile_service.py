"""
Unit Tests: Profile Service
Verifies user profile lifecycle, photo generation, and dual-store lookup in an isolated test sandbox.
"""
import unittest
import os
import tempfile
import shutil

from services.profile_service import ProfileService
from db.user_store import UserStore
from db.sync_manager import SyncManager
from vision.capture import FaceCapture


class TestProfileService(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_file = os.path.join(self.temp_dir, "profiles.json")
        self.sync_file = os.path.join(self.temp_dir, "sync_queue.json")
        self.user_store = UserStore(local_file=self.profiles_file, db=False)
        self.sync_mgr = SyncManager(local_queue_file=self.sync_file, db=False)
        self.face_cap = FaceCapture(save_dir=self.temp_dir)
        self.service = ProfileService(
            user_store=self.user_store,
            face_capture=self.face_cap,
            sync_manager=self.sync_mgr,
            captures_dir=self.temp_dir
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_lookup_profile(self):
        user_data = {
            'name': 'Rohan Mehra',
            'age': '26',
            'address': 'Chandigarh',
            'job': 'Product Manager',
            'gender': 'Male',
            'consent': 'Yes'
        }

        saved = self.service.save_profile(user_data)
        self.assertIsNotNone(saved.get('user_id'))
        self.assertEqual(saved['name'], 'Rohan Mehra')
        self.assertTrue(os.path.exists(saved['photo_path']))

        # Lookup by exact name
        found = self.service.lookup_profile(name_query='Rohan Mehra')
        self.assertIsNotNone(found)
        self.assertEqual(found['name'], 'Rohan Mehra')
        self.assertEqual(found['job'], 'Product Manager')

        # Lookup by partial name
        found_partial = self.service.lookup_profile(name_query='rohan')
        self.assertIsNotNone(found_partial)
        self.assertEqual(found_partial['name'], 'Rohan Mehra')

    def test_auto_fetch_db_and_get_all_users(self):
        user_data = {
            'name': 'Ashish Ojha',
            'age': '26',
            'address': 'Mumbai, India',
            'job': 'Software Engineer',
            'gender': 'Male',
            'consent': 'Yes'
        }
        saved = self.service.save_profile(user_data)
        user_id = saved['user_id']
        
        # 1. Verify get_all_users
        all_users = self.user_store.get_all_users()
        self.assertEqual(len(all_users), 1)
        self.assertEqual(all_users[0]['name'], 'Ashish Ojha')

        # 2. Verify auto-fetch by user_id
        fetched = self.service.lookup_profile(user_id=user_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched['user_id'], user_id)
        self.assertEqual(fetched['name'], 'Ashish Ojha')
        self.assertEqual(fetched['age'], '26')
        self.assertEqual(fetched['job'], 'Software Engineer')
        self.assertEqual(fetched['address'], 'Mumbai, India')
        self.assertEqual(fetched['gender'], 'Male')

        # 3. Verify last_seen update
        self.user_store.update_last_seen(user_id)
        updated = self.user_store.get_user_by_id(user_id)
        self.assertIsNotNone(updated['last_seen'])
        self.assertGreaterEqual(updated['conversation_count'], 2)


if __name__ == '__main__':
    unittest.main()

