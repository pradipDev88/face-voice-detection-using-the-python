"""
Unit Tests: Registration Agent & State Machine
Verifies multi-step registration, entity extraction, in-session corrections, skipping, and cancellation in an isolated sandbox.
"""
import unittest
import os
import tempfile
import shutil

from ai.registration_agent import RegistrationAgent, RegistrationState
from ai.brain import AIBrain
from services.profile_service import ProfileService
from db.user_store import UserStore
from db.sync_manager import SyncManager
from vision.capture import FaceCapture


class TestRegistrationAgent(unittest.TestCase):

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
        self.agent = RegistrationAgent(profile_service=self.profile_service)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_registration_flow_english(self):
        # 1. Start flow
        prompt, _ = self.agent.start_flow(initial_lang='en')
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_NAME)
        self.assertIn("full name", prompt.lower())

        # 2. Provide name
        resp, finished = self.agent.process_step("My name is John Doe")
        self.assertFalse(finished)
        self.assertEqual(self.agent.profile_data['name'], "John Doe")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_AGE)

        # 3. Provide age
        resp, finished = self.agent.process_step("I am twenty eight years old")
        self.assertFalse(finished)
        self.assertEqual(self.agent.profile_data['age'], "28")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_ADDRESS)

        # 4. Provide address
        resp, finished = self.agent.process_step("I live in New York")
        self.assertFalse(finished)
        self.assertEqual(self.agent.profile_data['address'], "New York")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_JOB)

        # 5. Provide job
        resp, finished = self.agent.process_step("I am a Data Scientist")
        self.assertFalse(finished)
        self.assertEqual(self.agent.profile_data['job'], "Data Scientist")
        self.assertEqual(self.agent.state, RegistrationState.AWAITING_CONFIRMATION)

        # 6. Confirm
        resp, finished = self.agent.process_step("Yes, save my profile")
        self.assertTrue(finished)
        self.assertEqual(self.agent.state, RegistrationState.COMPLETED)

    def test_full_registration_flow_hinglish(self):
        self.agent.start_flow(initial_lang='hinglish')

        # Name
        self.agent.process_step("Mera naam Anjali Sharma hai")
        self.assertEqual(self.agent.profile_data['name'], "Anjali Sharma")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_AGE)

        # Age
        self.agent.process_step("Meri umar chaubees saal hai")
        self.assertEqual(self.agent.profile_data['age'], "24")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_ADDRESS)

        # Address
        self.agent.process_step("Main Pune me rehta hoon")
        self.assertEqual(self.agent.profile_data['address'], "Pune")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_JOB)

        # Job
        self.agent.process_step("Mai Software Developer hu")
        self.assertEqual(self.agent.profile_data['job'], "Software Developer")
        self.assertEqual(self.agent.state, RegistrationState.AWAITING_CONFIRMATION)

        # Confirm
        resp, finished = self.agent.process_step("Haan bilkul save kar do")
        self.assertTrue(finished)
        self.assertEqual(self.agent.state, RegistrationState.COMPLETED)

    def test_in_flight_correction(self):
        self.agent.start_flow(initial_lang='en')
        self.agent.process_step("My name is Alex")
        self.assertEqual(self.agent.profile_data['name'], "Alex")

        # In-flight correction: "Actually my name is Alexander"
        resp, finished = self.agent.process_step("Actually change my name to Alexander")
        self.assertEqual(self.agent.profile_data['name'], "Alexander")
        self.assertFalse(finished)

    def test_skip_optional_field(self):
        self.agent.start_flow(initial_lang='en')
        self.agent.process_step("David")
        self.agent.process_step("30")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_ADDRESS)

        # Skip address
        resp, finished = self.agent.process_step("Skip this field")
        self.assertEqual(self.agent.profile_data['address'], "Not specified")
        self.assertEqual(self.agent.state, RegistrationState.COLLECTING_JOB)

    def test_cancellation(self):
        self.agent.start_flow(initial_lang='en')
        self.agent.process_step("David")
        resp, finished = self.agent.process_step("Cancel this registration")
        self.assertTrue(finished)
        self.assertEqual(self.agent.state, RegistrationState.CANCELLED)
        self.assertFalse(self.agent.is_active())


if __name__ == '__main__':
    unittest.main()

