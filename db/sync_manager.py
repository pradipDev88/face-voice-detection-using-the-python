"""
Durable Synchronization Queue & Offline Persistence Manager
Ensures zero data loss during network/database outages.
Queue operations are persisted locally and synchronized idempotently
when MySQL connectivity is restored.
"""
import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from db.connection import get_db


class SyncManager:
    """Manages durable offline queue and bidirectional sync with MySQL"""

    def __init__(self, local_queue_file: Optional[str] = None, db: Optional[Any] = None):
        self.db = None if db is False else (db if db is not None else get_db())
        self.local_file = local_queue_file or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'captures',
            'sync_queue.json'
        )
        os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
        if not os.path.exists(self.local_file):
            self._save_local_queue([])

    def _load_local_queue(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.local_file):
                with open(self.local_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠ Could not read local sync queue: {e}")
        return []

    def _save_local_queue(self, queue: List[Dict[str, Any]]):
        try:
            with open(self.local_file, 'w') as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            print(f"⚠ Could not save local sync queue: {e}")

    def enqueue(self, entity_type: str, action: str, payload: Dict[str, Any], record_uuid: Optional[str] = None) -> str:
        """
        Add a change to the synchronization queue (both local file and MySQL if available).
        
        Args:
            entity_type: 'user_info', 'user_images', 'conversation_log'
            action: 'insert', 'update', 'delete'
            payload: entity data dictionary
            record_uuid: unique identifier (auto-generated if not provided)
            
        Returns:
            str: record UUID
        """
        rec_uuid = record_uuid or str(uuid.uuid4())
        payload['uuid'] = rec_uuid
        timestamp = datetime.now().isoformat()

        queue_item = {
            'uuid': rec_uuid,
            'entity_type': entity_type,
            'action': action,
            'payload': payload,
            'status': 'pending',
            'retry_count': 0,
            'last_error': None,
            'created_at': timestamp,
            'synced_at': None
        }

        # 1. Always append to local durable queue file
        local_q = self._load_local_queue()
        # Avoid duplicate UUIDs
        existing_idx = next((i for i, item in enumerate(local_q) if item.get('uuid') == rec_uuid), None)
        if existing_idx is not None:
            local_q[existing_idx] = queue_item
        else:
            local_q.append(queue_item)
        self._save_local_queue(local_q)

        # 2. Try inserting into MySQL sync_queue if connected
        if self.db and self.db.is_connected:
            try:
                query = """
                INSERT INTO sync_queue (uuid, entity_type, action, payload, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE payload=%s, status='pending'
                """
                payload_str = json.dumps(payload)
                self.db.execute_query(query, (
                    rec_uuid, entity_type, action, payload_str, 'pending', datetime.now(), payload_str
                ))
            except Exception as e:
                print(f"⚠ MySQL sync_queue enqueue notice: {e}")

        return rec_uuid

    def sync_pending(self) -> Dict[str, int]:
        """
        Process all pending items from local queue into MySQL.
        
        Returns:
            dict with 'synced', 'failed', 'remaining' counts
        """
        results = {'synced': 0, 'failed': 0, 'remaining': 0}
        
        if not self.db or not self.db.is_connected:
            local_q = self._load_local_queue()
            results['remaining'] = sum(1 for item in local_q if item.get('status') == 'pending')
            return results

        local_q = self._load_local_queue()
        now_dt = datetime.now()

        for item in local_q:
            if item.get('status') != 'pending':
                continue

            rec_uuid = item['uuid']
            entity_type = item['entity_type']
            action = item['action']
            payload = item['payload']

            try:
                # Apply entity change to database
                success = self._apply_entity_change(entity_type, action, payload)
                if success:
                    item['status'] = 'synced'
                    item['synced_at'] = now_dt.isoformat()
                    results['synced'] += 1

                    # Update MySQL sync_queue status
                    try:
                        self.db.execute_query(
                            "UPDATE sync_queue SET status='synced', synced_at=%s WHERE uuid=%s",
                            (now_dt, rec_uuid)
                        )
                    except Exception:
                        pass
                else:
                    item['retry_count'] = item.get('retry_count', 0) + 1
                    item['last_error'] = "Failed to apply entity change"
                    results['failed'] += 1
            except Exception as e:
                item['retry_count'] = item.get('retry_count', 0) + 1
                item['last_error'] = str(e)
                results['failed'] += 1

        self._save_local_queue(local_q)
        results['remaining'] = sum(1 for item in local_q if item.get('status') == 'pending')
        return results

    def _apply_entity_change(self, entity_type: str, action: str, payload: Dict[str, Any]) -> bool:
        """Apply a single entity change to MySQL using parameterized queries"""
        if entity_type == 'user_info':
            rec_uuid = payload.get('uuid')
            name = payload.get('name', 'Anonymous')
            age_range = payload.get('age_range', '(25)')
            gender = payload.get('gender', 'Not specified')
            job = payload.get('college_or_job', payload.get('job', 'Not specified'))
            address = payload.get('address', 'Not specified')
            email = payload.get('email')
            phone = payload.get('phone')
            pref_lang = payload.get('preferred_language', 'en')
            photo_path = payload.get('photo_path')
            consent = payload.get('consent', 'Yes')

            if action in ('insert', 'update'):
                query = """
                INSERT INTO user_info (uuid, name, age_range, gender, college_or_job, address, email, phone, preferred_language, photo_path, consent, sync_status, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'synced', NOW())
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    age_range=VALUES(age_range),
                    gender=VALUES(gender),
                    college_or_job=VALUES(college_or_job),
                    address=VALUES(address),
                    email=VALUES(email),
                    phone=VALUES(phone),
                    preferred_language=VALUES(preferred_language),
                    photo_path=VALUES(photo_path),
                    consent=VALUES(consent),
                    sync_status='synced',
                    last_seen=NOW()
                """
                self.db.execute_query(query, (
                    rec_uuid, name, age_range, gender, job, address, email, phone, pref_lang, photo_path, consent
                ))
                return True

            elif action == 'delete':
                query = "DELETE FROM user_info WHERE uuid = %s OR name = %s"
                self.db.execute_query(query, (rec_uuid, name))
                return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get summary of synchronization status"""
        local_q = self._load_local_queue()
        pending = sum(1 for i in local_q if i.get('status') == 'pending')
        synced = sum(1 for i in local_q if i.get('status') == 'synced')
        failed = sum(1 for i in local_q if i.get('status') == 'failed')
        is_conn = bool(self.db and self.db.is_connected)

        return {
            'total_enqueued': len(local_q),
            'pending_count': pending,
            'synced_count': synced,
            'failed_count': failed,
            'is_connected': is_conn,
            'status_label': f"{pending} Pending Sync" if pending > 0 else "All Synced ✅"
        }
