"""
Unit Tests for Admin Service and Web Admin
"""
import unittest
import tempfile
import shutil
import os
import json
from unittest.mock import MagicMock, patch

from services.admin_service import AdminService
from services.profile_service import ProfileService
from db.user_store import UserStore
from db.sync_manager import SyncManager


class TestAdminService(unittest.TestCase):
    """Test AdminService data aggregation and management features"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_path = os.path.join(self.temp_dir, "profiles.json")
        self.sync_path = os.path.join(self.temp_dir, "sync_queue.json")

        initial_profiles = [
            {
                "id": 1001,
                "uuid": "user-1001",
                "name": "Jane Smith",
                "age_range": "(28)",
                "gender": "Female",
                "college_or_job": "Data Scientist",
                "address": "Bangalore",
                "email": "jane@example.com",
                "phone": "+91 9123456789",
                "preferred_language": "en",
                "photo_path": "",
                "sync_status": "synced"
            },
            {
                "id": 1002,
                "uuid": "user-1002",
                "name": "Rahul Verma",
                "age_range": "(32)",
                "gender": "Male",
                "college_or_job": "Architect",
                "address": "Mumbai",
                "email": "rahul@example.com",
                "phone": "+91 9988776655",
                "preferred_language": "hi",
                "photo_path": "",
                "sync_status": "pending"
            }
        ]
        with open(self.profiles_path, "w", encoding="utf-8") as f:
            json.dump(initial_profiles, f)

        with open(self.sync_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        self.mock_store = UserStore(local_file=self.profiles_path, db=False)
        self.mock_sync = SyncManager(local_queue_file=self.sync_path, db=False)
        self.profile_service = ProfileService(
            user_store=self.mock_store,
            captures_dir=self.temp_dir,
            sync_manager=self.mock_sync
        )

        self.admin = AdminService(
            profile_service=self.profile_service,
            sync_manager=self.mock_sync
        )
        self.admin.db = None

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_overview_stats(self):
        stats = self.admin.get_overview_stats()
        self.assertIn('total_users', stats)
        self.assertIn('total_conversations', stats)
        self.assertIn('total_sessions', stats)
        self.assertIn('pending_sync', stats)
        self.assertIn('ai_provider', stats)
        self.assertGreaterEqual(stats['total_users'], 2)

    def test_get_all_users_and_search_filter(self):
        all_users = self.admin.get_all_users()
        self.assertGreaterEqual(len(all_users), 2)

        # Filter by name
        filtered = self.admin.get_all_users(search_query="Jane")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['name'], "Jane Smith")

        # Filter by city
        mumbai_users = self.admin.get_all_users(search_query="Mumbai")
        self.assertEqual(len(mumbai_users), 1)
        self.assertEqual(mumbai_users[0]['name'], "Rahul Verma")

        # Filter by non-existent query
        none_users = self.admin.get_all_users(search_query="NonExistentPerson")
        self.assertEqual(len(none_users), 0)

    def test_save_and_delete_user(self):
        new_user = {
            "name": "Amit Kumar",
            "age": "24",
            "gender": "Male",
            "college_or_job": "Engineer",
            "address": "Delhi",
            "email": "amit@test.com",
            "phone": "+91 9000000000"
        }
        saved = self.admin.save_user(new_user)
        self.assertIsNotNone(saved)
        self.assertEqual(saved['name'], "Amit Kumar")

        # Check user exists
        found = self.admin.get_all_users(search_query="Amit")
        self.assertEqual(len(found), 1)

        # Delete user
        del_success = self.admin.delete_user(saved['id'])
        self.assertTrue(del_success)

        # Verify deleted
        found_after = self.admin.get_all_users(search_query="Amit")
        self.assertEqual(len(found_after), 0)

    def test_export_all_data(self):
        export = self.admin.export_all_data()
        self.assertIn('metadata', export)
        self.assertIn('users', export)
        self.assertIn('conversation_logs', export)
        self.assertIn('registration_sessions', export)
        self.assertIn('sync_queue', export)
        self.assertGreaterEqual(len(export['users']), 2)


if __name__ == '__main__':
    unittest.main()
