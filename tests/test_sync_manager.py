"""
Unit Tests: Sync Manager & Durable Local Queue
Verifies offline persistence, enqueuing, idempotent deduplication,
and queue status reporting.
"""
import unittest
import os
import tempfile
import json
from db.sync_manager import SyncManager


class TestSyncManager(unittest.TestCase):

    def setUp(self):
        # Create a unique temporary queue file for isolated testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_queue_file = os.path.join(self.temp_dir, 'test_sync_queue.json')
        self.sync_manager = SyncManager(local_queue_file=self.temp_queue_file)

    def tearDown(self):
        if os.path.exists(self.temp_queue_file):
            os.remove(self.temp_queue_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_enqueue_offline_record(self):
        payload = {
            'name': 'Pooja Verma',
            'age': '29',
            'city': 'Delhi',
            'job': 'Architect'
        }
        rec_uuid = self.sync_manager.enqueue(
            entity_type='user_info',
            action='insert',
            payload=payload,
            record_uuid='test-uuid-101'
        )
        self.assertEqual(rec_uuid, 'test-uuid-101')

        # Verify file content
        with open(self.temp_queue_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uuid'], 'test-uuid-101')
        self.assertEqual(data[0]['status'], 'pending')
        self.assertEqual(data[0]['payload']['name'], 'Pooja Verma')

    def test_idempotent_enqueue_update(self):
        payload1 = {'name': 'Pooja Verma', 'age': '29'}
        self.sync_manager.enqueue(
            entity_type='user_info',
            action='insert',
            payload=payload1,
            record_uuid='test-uuid-101'
        )

        payload2 = {'name': 'Pooja Verma', 'age': '30'}
        self.sync_manager.enqueue(
            entity_type='user_info',
            action='update',
            payload=payload2,
            record_uuid='test-uuid-101'
        )

        # Should update existing item rather than duplicating
        status = self.sync_manager.get_status()
        self.assertEqual(status['total_enqueued'], 1)
        self.assertEqual(status['pending_count'], 1)

        with open(self.temp_queue_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['payload']['age'], '30')

    def test_get_status(self):
        self.sync_manager.enqueue('user_info', 'insert', {'name': 'User 1'}, record_uuid='u-1')
        self.sync_manager.enqueue('user_info', 'insert', {'name': 'User 2'}, record_uuid='u-2')

        status = self.sync_manager.get_status()
        self.assertEqual(status['total_enqueued'], 2)
        self.assertEqual(status['pending_count'], 2)


if __name__ == '__main__':
    unittest.main()
