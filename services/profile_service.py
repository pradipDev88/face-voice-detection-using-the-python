"""
Profile Service Layer
Handles user profile lifecycle, persistence into MySQL and offline JSON cache,
real-time lookup, photo capture, editing, deletion, data export, and sync management.
"""
import os
import json
import re
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
import cv2

from db.user_store import UserStore
from db.sync_manager import SyncManager


class ProfileService:
    """Service layer managing user profiles, photos, and sync"""

    def __init__(self, user_store: Optional[UserStore] = None, face_capture=None, face_embeddings=None, sync_manager: Optional[SyncManager] = None, captures_dir: Optional[str] = None):
        self.user_store = user_store or UserStore()
        self.sync_manager = sync_manager or SyncManager()
        self.face_capture = face_capture
        self.face_embeddings = face_embeddings
        self.captures_dir = captures_dir or 'captures'
        self.listeners: List[Callable[[Dict[str, Any]], None]] = []
        self.offline_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'captures',
            'profiles.json'
        )

    def subscribe(self, listener: Callable[[Dict[str, Any]], None]):
        """Subscribe a listener (e.g. UI) to profile events"""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def notify(self, profile: Dict[str, Any]):
        """Notify subscribers of profile changes"""
        for listener in self.listeners:
            try:
                listener(profile)
            except Exception as e:
                print(f"⚠ Profile notification error: {e}")

    def save_profile(self, data: Dict[str, Any], frame=None) -> Dict[str, Any]:
        """
        Validate, take photo snapshot, save to MySQL and offline backup,
        and enqueue in durable synchronization queue.
        
        Args:
            data: dict containing name, age, address, job, gender, consent, email, phone
            frame: optional current OpenCV frame
            
        Returns:
            dict containing saved user record
        """
        rec_uuid = data.get('uuid') or str(uuid.uuid4())
        name = str(data.get('name', 'Anonymous')).strip().title()
        age = str(data.get('age', '25')).strip()
        address = str(data.get('address', 'Not specified')).strip().title()
        job = str(data.get('job', 'Not specified')).strip().title()
        gender = str(data.get('gender', 'Not specified')).strip()
        consent = str(data.get('consent', 'Yes')).strip()
        email = data.get('email', '')
        phone = data.get('phone', '')
        pref_lang = data.get('preferred_language', 'en')

        # 1. Capture photo
        photo_path = data.get('photo_path')
        if not photo_path or not os.path.exists(photo_path):
            photo_path = self.capture_profile_photo(name, frame)

        # 2. Extract embedding if possible
        embedding = data.get('embedding')
        if embedding is None and self.face_embeddings and os.path.exists(photo_path):
            try:
                img = cv2.imread(photo_path)
                if img is not None:
                    embedding = self.face_embeddings.get_embedding(img)
            except Exception as e:
                print(f"⚠ Embedding extraction error: {e}")

        # 3. Save to UserStore (MySQL + offline backup)
        user_id = self.user_store.create_user(
            name=name,
            age_range=f"({age})",
            gender=gender,
            college_or_job=job,
            address=address,
            photo_path=photo_path,
            consent=consent
        )

        if embedding is not None and user_id:
            try:
                self.user_store.save_user_image(
                    user_id=user_id,
                    file_path=photo_path,
                    embedding=embedding,
                    is_primary=True
                )
            except Exception as e:
                print(f"⚠ Image embedding save error: {e}")

        saved_record = {
            'user_id': user_id,
            'uuid': rec_uuid,
            'name': name,
            'age': age,
            'address': address,
            'job': job,
            'gender': gender,
            'email': email,
            'phone': phone,
            'preferred_language': pref_lang,
            'photo_path': photo_path,
            'consent': consent,
            'sync_status': 'synced' if (self.user_store.db and self.user_store.db.is_connected) else 'pending',
            'created_at': datetime.now().isoformat()
        }

        # 4. Enqueue in sync manager for durable tracking
        self.sync_manager.enqueue(
            entity_type='user_info',
            action='insert',
            payload=saved_record,
            record_uuid=rec_uuid
        )

        # 5. Notify UI listeners
        self.notify(saved_record)
        return saved_record

    def edit_profile(self, user_id_or_name: Any, updates: Dict[str, Any]) -> bool:
        """Edit an existing user profile"""
        profile = self.lookup_profile(
            name_query=str(user_id_or_name) if isinstance(user_id_or_name, str) else None,
            user_id=int(user_id_or_name) if isinstance(user_id_or_name, int) else None
        )
        if not profile:
            return False

        profile.update(updates)
        uid = profile.get('user_id')
        rec_uuid = profile.get('uuid') or str(uuid.uuid4())

        # Update MySQL
        if self.user_store.db and self.user_store.db.is_connected and uid:
            try:
                query = """
                UPDATE user_info
                SET name=%s, age_range=%s, college_or_job=%s, address=%s, last_seen=NOW()
                WHERE id=%s
                """
                age_range = f"({profile.get('age', '25')})"
                self.user_store.db.execute_query(query, (
                    profile['name'], age_range, profile['job'], profile['address'], uid
                ))
            except Exception as e:
                print(f"⚠ MySQL edit profile error: {e}")

        # Update offline JSON
        profiles = self.user_store._load_local_profiles()
        for p in profiles:
            if str(p.get('id')) == str(uid) or p.get('name', '').lower() == profile['name'].lower():
                p.update(profile)
                break
        self.user_store._save_local_profiles(profiles)

        # Enqueue update
        self.sync_manager.enqueue(
            entity_type='user_info',
            action='update',
            payload=profile,
            record_uuid=rec_uuid
        )
        self.notify(profile)
        return True

    def delete_profile(self, user_id_or_name: Any) -> bool:
        """Delete an existing user profile"""
        profile = self.lookup_profile(
            name_query=str(user_id_or_name) if isinstance(user_id_or_name, str) else None,
            user_id=int(user_id_or_name) if isinstance(user_id_or_name, int) else None
        )
        if not profile:
            return False

        uid = profile.get('user_id')
        name = profile.get('name')
        rec_uuid = profile.get('uuid') or str(uuid.uuid4())

        # Delete from MySQL
        if self.user_store.db and self.user_store.db.is_connected and uid:
            try:
                self.user_store.db.execute_query("DELETE FROM user_info WHERE id = %s", (uid,))
            except Exception as e:
                print(f"⚠ MySQL delete error: {e}")

        # Delete from local JSON
        profiles = self.user_store._load_local_profiles()
        profiles = [p for p in profiles if str(p.get('id')) != str(uid) and p.get('name', '').lower() != name.lower()]
        self.user_store._save_local_profiles(profiles)

        # Enqueue delete
        self.sync_manager.enqueue(
            entity_type='user_info',
            action='delete',
            payload={'uuid': rec_uuid, 'name': name},
            record_uuid=rec_uuid
        )
        return True

    def export_profiles(self, format: str = 'json') -> str:
        """Export all profiles as JSON string"""
        profiles = self.user_store._load_local_profiles()
        return json.dumps(profiles, indent=2)

    def sync_offline(self) -> Dict[str, int]:
        """Trigger synchronization of offline queue"""
        return self.sync_manager.sync_pending()

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return self.sync_manager.get_status()

    def lookup_profile(self, name_query: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Search for an existing profile by name or ID.
        Checks MySQL first, falls back to local JSON store.
        """
        # Search by ID
        if user_id is not None:
            user = self.user_store.get_user_by_id(user_id)
            if user:
                return {
                    'user_id': user.get('id') or user.get('user_id'),
                    'uuid': user.get('uuid') or f"user-{user.get('id')}",
                    'name': user.get('name'),
                    'age': str(user.get('age_range', '')).strip('()') if user.get('age_range') else str(user.get('age', '')),
                    'gender': user.get('gender', 'Not specified'),
                    'job': user.get('college_or_job') or user.get('job', 'Not specified'),
                    'address': user.get('address', 'Not specified'),
                    'email': user.get('email', ''),
                    'phone': user.get('phone', ''),
                    'preferred_language': user.get('preferred_language', 'en'),
                    'photo_path': user.get('photo_path', ''),
                    'consent': user.get('consent', 'Yes'),
                    'sync_status': user.get('sync_status', 'synced' if (self.user_store.db and self.user_store.db.is_connected) else 'pending')
                }

        # Search by Name
        if name_query:
            clean_query = name_query.strip().lower()
            
            # 1. Search MySQL
            if self.user_store.db and self.user_store.db.is_connected:
                try:
                    query = "SELECT * FROM user_info WHERE LOWER(name) LIKE %s LIMIT 1"
                    res = self.user_store.db.fetch_all(query, (f"%{clean_query}%",))
                    if res:
                        row = res[0]
                        return {
                            'user_id': row.get('id') or row.get('user_id'),
                            'uuid': row.get('uuid'),
                            'name': row.get('name'),
                            'age': str(row.get('age_range', '')).strip('()'),
                            'gender': row.get('gender'),
                            'job': row.get('college_or_job'),
                            'address': row.get('address', 'Not specified'),
                            'email': row.get('email'),
                            'phone': row.get('phone'),
                            'preferred_language': row.get('preferred_language', 'en'),
                            'photo_path': row.get('photo_path', ''),
                            'consent': row.get('consent'),
                            'sync_status': row.get('sync_status', 'synced')
                        }
                except Exception as e:
                    print(f"⚠ MySQL lookup error: {e}")

            # 2. Search local offline JSON
            local_profiles = self.user_store._load_local_profiles()
            for p in local_profiles:
                p_name = p.get('name', '').lower()
                if clean_query in p_name or p_name in clean_query:
                    return {
                        'user_id': p.get('id'),
                        'uuid': p.get('uuid'),
                        'name': p.get('name'),
                        'age': str(p.get('age_range', '')).strip('()'),
                        'gender': p.get('gender'),
                        'job': p.get('college_or_job'),
                        'address': p.get('address', 'Not specified'),
                        'email': p.get('email'),
                        'phone': p.get('phone'),
                        'preferred_language': p.get('preferred_language', 'en'),
                        'photo_path': p.get('photo_path', ''),
                        'consent': p.get('consent'),
                        'sync_status': p.get('sync_status', 'pending')
                    }

        return None

    def capture_profile_photo(self, name: str, frame=None) -> str:
        """Capture screenshot from frame or camera, or generate placeholder badge"""
        cap_dir = getattr(self, 'captures_dir', 'captures')
        os.makedirs(cap_dir, exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower().strip())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_profile_{timestamp}.jpg"
        filepath = os.path.join(cap_dir, filename)

        img = None
        if frame is not None:
            img = frame.copy()
        else:
            try:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, f = cap.read()
                    if ret:
                        img = f
                    cap.release()
            except Exception:
                pass

        if img is None:
            import numpy as np
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(img, f"Profile: {name}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.putText(img, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", (50, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)

        cv2.imwrite(filepath, img)
        return filepath
