"""
Admin Service Module
Provides unified data aggregation, filtering, CRUD operations,
and telemetry across all 6 tables and offline stores for the Admin Dashboard.
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from db.connection import get_db
from db.sync_manager import SyncManager
from services.profile_service import ProfileService
from services.health_service import HealthService


class AdminService:
    """Aggregates multi-table records and controls for the Admin Dashboard"""

    def __init__(self, profile_service: Optional[ProfileService] = None, sync_manager: Optional[SyncManager] = None):
        self.db = get_db()
        self.profile_service = profile_service or ProfileService()
        self.sync_manager = sync_manager or SyncManager()
        self.health_service = HealthService()

    def get_overview_stats(self) -> Dict[str, Any]:
        """Aggregate high-level system telemetry and record counts"""
        total_users = 0
        total_convos = 0
        total_sessions = 0
        db_connected = bool(self.db and self.db.is_connected)
        latency_ms = 0

        # 1. Database metrics
        if db_connected:
            try:
                t0 = time.time()
                res = self.db.fetch_one("SELECT COUNT(*) as count FROM user_info")
                latency_ms = int((time.time() - t0) * 1000)
                if res:
                    total_users = res.get('count', 0)

                conv_res = self.db.fetch_one("SELECT COUNT(*) as count FROM conversation_log")
                if conv_res:
                    total_convos = conv_res.get('count', 0)

                sess_res = self.db.fetch_one("SELECT COUNT(*) as count FROM registration_sessions")
                if sess_res:
                    total_sessions = sess_res.get('count', 0)
            except Exception as e:
                print(f"⚠ Admin DB stats error: {e}")
                db_connected = False

        # Fallback to local files if MySQL is offline or returned 0
        if not db_connected or total_users == 0:
            local_profiles = self.profile_service.user_store._load_local_profiles()
            total_users = max(total_users, len(local_profiles))
        if not db_connected or total_convos == 0:
            cap_dir = getattr(self.profile_service, 'captures_dir', 'captures')
            log_file = os.path.join(cap_dir, 'conversation_logs.json')
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        total_convos = max(total_convos, len(json.load(f)))
                except Exception:
                    pass
        if not db_connected or total_sessions == 0:
            cap_dir = getattr(self.profile_service, 'captures_dir', 'captures')
            sess_file = os.path.join(cap_dir, 'sessions.json')
            if os.path.exists(sess_file):
                try:
                    with open(sess_file, 'r', encoding='utf-8') as f:
                        total_sessions = max(total_sessions, len(json.load(f)))
                except Exception:
                    pass

        # 2. Sync queue metrics
        sync_status = self.sync_manager.get_status()
        pending_sync = sync_status.get('pending_count', 0)

        # 3. AI provider health
        health = self.health_service.check_health()
        ai_provider = health.get('components', {}).get('ai_provider', {}).get('provider', 'Local Brain')
        ai_status = health.get('components', {}).get('ai_provider', {}).get('status', 'healthy')

        # 4. Storage photo count
        captures_dir = getattr(self.profile_service, 'captures_dir', 'captures')
        photo_count = 0
        if os.path.exists(captures_dir):
            photo_count = len([f for f in os.listdir(captures_dir) if f.lower().endswith('.jpg')])

        return {
            'total_users': total_users,
            'total_conversations': total_convos,
            'total_sessions': total_sessions,
            'pending_sync': pending_sync,
            'db_connected': db_connected,
            'db_latency_ms': latency_ms,
            'ai_provider': ai_provider,
            'ai_status': ai_status,
            'photo_count': photo_count,
            'timestamp': datetime.now().isoformat()
        }

    def get_all_users(self, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all users across MySQL and local fallback JSON"""
        users: List[Dict[str, Any]] = []

        if self.db and self.db.is_connected:
            try:
                query = "SELECT * FROM user_info ORDER BY id ASC"
                rows = self.db.fetch_all(query)
                for r in rows:
                    users.append({
                        'id': r.get('id'),
                        'uuid': r.get('uuid') or f"user-{r.get('id')}",
                        'name': r.get('name', 'Anonymous'),
                        'age': str(r.get('age_range', '--')).strip('()'),
                        'gender': r.get('gender', 'Not specified'),
                        'college_or_job': r.get('college_or_job', 'Not specified'),
                        'address': r.get('address', 'Not specified'),
                        'email': r.get('email', '--'),
                        'phone': r.get('phone', '--'),
                        'preferred_language': r.get('preferred_language', 'en'),
                        'photo_path': r.get('photo_path', ''),
                        'consent': r.get('consent', 'Yes'),
                        'sync_status': r.get('sync_status', 'synced'),
                        'last_seen': str(r.get('last_seen', '--'))
                    })
            except Exception as e:
                print(f"⚠ Admin fetch MySQL users error: {e}")

        # Fallback to local profiles
        if not users:
            for p in self.profile_service.user_store._load_local_profiles():
                users.append({
                    'id': p.get('id', 1000),
                    'uuid': p.get('uuid', f"user-{p.get('id', 1000)}"),
                    'name': p.get('name', 'Anonymous'),
                    'age': str(p.get('age_range', '--')).strip('()'),
                    'gender': p.get('gender', 'Not specified'),
                    'college_or_job': p.get('college_or_job', 'Not specified'),
                    'address': p.get('address', 'Not specified'),
                    'email': p.get('email', '--'),
                    'phone': p.get('phone', '--'),
                    'preferred_language': p.get('preferred_language', 'en'),
                    'photo_path': p.get('photo_path', ''),
                    'consent': p.get('consent', 'Yes'),
                    'sync_status': p.get('sync_status', 'pending'),
                    'last_seen': str(p.get('last_seen', '--'))
                })

        # Apply search filter
        if search_query and search_query.strip():
            sq = search_query.strip().lower()
            users = [
                u for u in users
                if sq in str(u.get('name', '')).lower()
                or sq in str(u.get('address', '')).lower()
                or sq in str(u.get('college_or_job', '')).lower()
                or sq in str(u.get('email', '')).lower()
                or sq in str(u.get('phone', '')).lower()
            ]

        return users

    def save_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a user profile through the ProfileService"""
        res = self.profile_service.save_profile(user_data)
        if res and 'user_id' in res and 'id' not in res:
            res['id'] = res['user_id']
        return res

    def delete_user(self, user_id_or_name: Any) -> bool:
        """Delete user profile from both MySQL and local store"""
        return self.profile_service.delete_profile(user_id_or_name)

    def get_conversation_logs(self, limit: int = 100, speaker: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve historical conversation turns from MySQL or session memory"""
        logs = []
        if self.db and self.db.is_connected:
            try:
                query = "SELECT * FROM conversation_log"
                params = []
                if speaker and speaker.lower() != 'all':
                    query += " WHERE speaker = %s"
                    params.append(speaker.capitalize())
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                
                rows = self.db.fetch_all(query, tuple(params))
                for r in rows:
                    logs.append({
                        'log_id': r.get('log_id'),
                        'user_id': r.get('user_id'),
                        'speaker': r.get('speaker'),
                        'message': r.get('message'),
                        'language': r.get('language', 'en'),
                        'intent': r.get('intent', '--'),
                        'confidence': round(float(r.get('confidence', 0.0) or 0.0), 2),
                        'timestamp': str(r.get('timestamp', '--'))
                    })
            except Exception as e:
                print(f"⚠ Admin fetch conversation logs error: {e}")

        if not logs:
            cap_dir = getattr(self.profile_service, 'captures_dir', 'captures')
            log_file = os.path.join(cap_dir, 'conversation_logs.json')
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        file_logs = json.load(f)
                        if speaker and speaker.lower() != 'all':
                            file_logs = [l for l in file_logs if str(l.get('speaker', '')).lower() == speaker.lower()]
                        logs = file_logs[-limit:]
                except Exception:
                    pass

        return logs

    def get_registration_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve stateful registration sessions from registration_sessions table or offline cache"""
        sessions = []
        if self.db and self.db.is_connected:
            try:
                query = "SELECT * FROM registration_sessions ORDER BY updated_at DESC LIMIT %s"
                rows = self.db.fetch_all(query, (limit,))
                for r in rows:
                    sessions.append({
                        'session_id': r.get('session_id'),
                        'user_id': r.get('user_id'),
                        'language': r.get('language', 'en'),
                        'current_state': r.get('current_state'),
                        'status': r.get('status'),
                        'collected_data': r.get('collected_data'),
                        'is_confirmed': bool(r.get('is_confirmed')),
                        'updated_at': str(r.get('updated_at', '--'))
                    })
            except Exception as e:
                print(f"⚠ Admin fetch sessions error: {e}")

        if not sessions:
            cap_dir = getattr(self.profile_service, 'captures_dir', 'captures')
            sess_file = os.path.join(cap_dir, 'sessions.json')
            if os.path.exists(sess_file):
                try:
                    with open(sess_file, 'r', encoding='utf-8') as f:
                        sessions = json.load(f)[-limit:]
                except Exception:
                    pass

        return sessions

    def get_sync_queue(self) -> List[Dict[str, Any]]:
        """Retrieve durable offline sync queue items"""
        # Load local durable queue
        return self.sync_manager._load_local_queue()

    def trigger_sync(self) -> Dict[str, int]:
        """Trigger immediate bidirectional sync to MySQL"""
        return self.sync_manager.sync_pending()

    def export_all_data(self) -> Dict[str, Any]:
        """Export full database state into a comprehensive dictionary"""
        return {
            'metadata': {
                'system': 'Mr. Beast AI Admin Export',
                'exported_at': datetime.now().isoformat()
            },
            'users': self.get_all_users(),
            'conversation_logs': self.get_conversation_logs(limit=500),
            'registration_sessions': self.get_registration_sessions(limit=100),
            'sync_queue': self.get_sync_queue()
        }
