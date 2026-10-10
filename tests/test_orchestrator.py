"""
Unit Tests: AI Orchestrator
Verifies end-to-end intent routing for Create Profile, Profile Lookup, and General Conversation in an isolated test environment.
"""
import unittest
import os
import tempfile
import shutil

from ai.orchestrator import AIOrchestrator
from services.profile_service import ProfileService
from db.user_store import UserStore
from db.sync_manager import SyncManager
from vision.capture import FaceCapture


class TestAIOrchestrator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_file = os.path.join(self.temp_dir, "profiles.json")
        self.sync_file = os.path.join(self.temp_dir, "sync_queue.json")
        self.user_store = UserStore(local_file=self.profiles_file, db=False)
        self.sync_mgr = SyncManager(local_queue_file=self.sync_file, db=False)
        self.face_cap = FaceCapture(save_dir=self.temp_dir)
        self.profile_service = ProfileService(
            user_store=self.user_store,
            face_capture=self.face_cap,
            sync_manager=self.sync_mgr,
            captures_dir=self.temp_dir
        )
        self.orch = AIOrchestrator(profile_service=self.profile_service)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_greeting_route(self):
        res = self.orch.handle_input("Hello Mr Beast")
        self.assertEqual(res['branch'], 'general_conversation')
        self.assertEqual(res['intent'], 'greeting')
        self.assertFalse(res['is_registration_active'])
        self.assertIn("Mr. Beast", res['response'])

    def test_create_profile_route(self):
        res = self.orch.handle_input("I want to create my profile")
        self.assertEqual(res['branch'], 'create_profile')
        self.assertEqual(res['intent'], 'create_profile')
        self.assertTrue(res['is_registration_active'])
        self.assertIn("full name", res['response'].lower())

    def test_create_profile_hinglish_route(self):
        orch = AIOrchestrator(profile_service=self.profile_service)
        res = orch.handle_input("Mera profile bana do")
        self.assertEqual(res['branch'], 'create_profile')
        self.assertTrue(res['is_registration_active'])
        self.assertEqual(res['language'], 'hinglish')
        self.assertIn("naam", res['response'].lower())

    def test_profile_lookup_route(self):
        # Save a test user first in the isolated store
        self.profile_service.save_profile({
            'name': 'Kavita Roy',
            'age': '29',
            'address': 'Kolkata',
            'job': 'Architect',
            'gender': 'Female'
        })

        res = self.orch.handle_input("Check profile of Kavita Roy")
        self.assertEqual(res['branch'], 'profile_lookup')
        self.assertIn("Kavita Roy", res['response'])
        self.assertIn("Kolkata", res['response'])


if __name__ == '__main__':
    unittest.main()

