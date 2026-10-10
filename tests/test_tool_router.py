"""
Unit Tests: Safe Tool Router
Verifies arithmetic evaluation safety, datetime formatting,
diagnostics execution, and confirmation gating on destructive actions.
"""
import unittest
import tempfile
import shutil
import os

from ai.tool_router import ToolRouter
from services.profile_service import ProfileService
from db.user_store import UserStore
from db.sync_manager import SyncManager


class TestToolRouter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_file = os.path.join(self.temp_dir, "profiles.json")
        self.sync_file = os.path.join(self.temp_dir, "sync_queue.json")
        self.user_store = UserStore(local_file=self.profiles_file, db=False)
        self.sync_mgr = SyncManager(local_queue_file=self.sync_file, db=False)
        self.profile_service = ProfileService(
            user_store=self.user_store,
            sync_manager=self.sync_mgr,
            captures_dir=self.temp_dir
        )
        self.router = ToolRouter(profile_service=self.profile_service)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_datetime(self):
        res = self.router.execute_tool('get_datetime')
        self.assertTrue(res['success'])
        self.assertIn("Today is", res['result'])

    def test_calculate_safe_math(self):
        res = self.router.execute_tool('calculate', expression='25 * 4 + 10')
        self.assertTrue(res['success'])
        self.assertIn("110", res['result'])

    def test_calculate_disallows_code_injection(self):
        res = self.router.execute_tool('calculate', expression='__import__("os").system("echo 1")')
        # Should cleanly return an error rather than executing code
        self.assertIn("Could not evaluate", res['result'])

    def test_delete_profile_requires_confirmation(self):
        # 1. Without confirmation
        res = self.router.execute_tool('delete_profile', name='Test User', confirmed=False)
        self.assertFalse(res.get('success'))
        self.assertTrue(res.get('needs_confirmation'))

    def test_unregistered_tool_rejected(self):
        res = self.router.execute_tool('unauthorized_shell_command')
        self.assertFalse(res['success'])
        self.assertIn("not registered", res['error'])


if __name__ == '__main__':
    unittest.main()
