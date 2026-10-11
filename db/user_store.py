"""
User Store Module
Handles all user-related database operations with offline JSON backup
"""
import os
import json
from datetime import datetime
from db.connection import get_db


class UserStore:
    """Manages user data in MySQL database with offline fallback"""
    
    def __init__(self, local_file=None, db=None):
        """Initialize user store with optional custom file/db for test isolation"""
        self.db = db if db is not None else get_db()
        self.local_file = local_file or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'captures', 'profiles.json')
        os.makedirs(os.path.dirname(self.local_file), exist_ok=True)
        if not os.path.exists(self.local_file):
            try:
                with open(self.local_file, 'w') as f:
                    json.dump([], f)
            except Exception:
                pass

    def _load_local_profiles(self):
        """Load profiles from local fallback JSON"""
        try:
            if os.path.exists(self.local_file):
                with open(self.local_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_local_profiles(self, profiles):
        """Save profiles to local fallback JSON"""
        try:
            with open(self.local_file, 'w') as f:
                json.dump(profiles, f, indent=2)
        except Exception as e:
            print(f"⚠ Could not save local profile backup: {e}")

    def create_user(self, name, age_range, gender, college_or_job, address='', photo_path='', consent='Yes'):
        """Create new user in MySQL and offline store"""
        now_str = datetime.now().isoformat()
        user_id = None
        
        # 1. Try MySQL
        if self.db and self.db.is_connected:
            try:
                # Try inserting with address and photo_path
                query = """
                INSERT INTO user_info (name, age_range, gender, college_or_job, address, photo_path, consent, first_seen, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (name, str(age_range), gender, college_or_job, address, photo_path, consent, datetime.now(), datetime.now())
                user_id = self.db.execute_query(query, params)
            except Exception:
                try:
                    query = """
                    INSERT INTO user_info (name, age_range, gender, college_or_job, consent, first_seen, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    params = (name, str(age_range), gender, college_or_job, consent, datetime.now(), datetime.now())
                    user_id = self.db.execute_query(query, params)
                except Exception as e:
                    print(f"⚠ MySQL insert error: {e}")

        # 2. Local fallback storage
        profiles = self._load_local_profiles()
        if user_id is None:
            user_id = len(profiles) + 1001

        profile_entry = {
            'id': user_id,
            'name': name,
            'age_range': str(age_range),
            'gender': gender,
            'college_or_job': college_or_job,
            'address': address,
            'photo_path': photo_path,
            'consent': consent,
            'created_at': now_str,
            'last_seen': now_str,
            'conversation_count': 1,
            'embeddings': []
        }
        
        # Update if exists or append
        existing_idx = next((i for i, p in enumerate(profiles) if p.get('name', '').lower() == name.lower()), None)
        if existing_idx is not None:
            profile_entry['embeddings'] = profiles[existing_idx].get('embeddings', [])
            profiles[existing_idx].update(profile_entry)
        else:
            profiles.append(profile_entry)
            
        self._save_local_profiles(profiles)
        print(f"✓ Profile saved: {name} (ID: {user_id}) [Local JSON + DB]")
        return user_id

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        if self.db and self.db.is_connected:
            try:
                query = "SELECT * FROM user_info WHERE id = %s"
                res = self.db.fetch_one(query, (user_id,))
                if res:
                    return res
            except Exception:
                pass
        
        # Fallback to local
        for p in self._load_local_profiles():
            if str(p.get('id')) == str(user_id):
                return p
        return None

    def get_user_by_name(self, name):
        """Get user by name"""
        if not name:
            return None
        if self.db and self.db.is_connected:
            try:
                query = "SELECT * FROM user_info WHERE name = %s"
                res = self.db.fetch_one(query, (name,))
                if res:
                    return res
            except Exception:
                pass
        
        # Fallback to local
        for p in self._load_local_profiles():
            if p.get('name', '').lower() == name.lower():
                return p
        return None

    def get_all_users(self):
        """Get all users across MySQL and local storage"""
        users = []
        seen_ids = set()
        if self.db and self.db.is_connected:
            try:
                query = "SELECT * FROM user_info ORDER BY id ASC"
                rows = self.db.fetch_all(query)
                for r in rows:
                    users.append(r)
                    seen_ids.add(str(r.get('id')))
            except Exception:
                pass

        for p in self._load_local_profiles():
            pid = str(p.get('id'))
            if pid not in seen_ids:
                users.append(p)
                seen_ids.add(pid)
        return users

    def update_last_seen(self, user_id):
        """Update user's last seen timestamp"""
        if self.db and self.db.is_connected:
            try:
                query = "UPDATE user_info SET last_seen = %s WHERE id = %s"
                self.db.execute_query(query, (datetime.now(), user_id))
            except Exception:
                pass
        
        profiles = self._load_local_profiles()
        for p in profiles:
            if str(p.get('id')) == str(user_id):
                p['last_seen'] = datetime.now().isoformat()
                p['conversation_count'] = p.get('conversation_count', 0) + 1
                break
        self._save_local_profiles(profiles)

    def save_user_image(self, user_id, file_path, embedding, is_primary=False):
        """Save user face image and embedding"""
        image_id = None
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        
        if self.db and self.db.is_connected:
            try:
                query = """
                INSERT INTO user_images (user_id, file_path, embedding, is_primary)
                VALUES (%s, %s, %s, %s)
                """
                embedding_json = json.dumps(embedding_list)
                image_id = self.db.execute_query(query, (user_id, file_path, embedding_json, is_primary))
            except Exception as e:
                print(f"⚠ MySQL image insert error: {e}")

        # Local storage
        profiles = self._load_local_profiles()
        for p in profiles:
            if str(p.get('id')) == str(user_id):
                p['photo_path'] = file_path
                if embedding_list is not None:
                    p.setdefault('embeddings', []).append(embedding_list)
                break
        self._save_local_profiles(profiles)
        print(f"✓ Image saved for user {user_id}: {file_path}")
        return image_id or 1

    def get_all_embeddings(self):
        """Get all user embeddings for matching (from DB and local file)"""
        results = []
        seen_user_ids = set()
        if self.db and self.db.is_connected:
            try:
                query = """
                SELECT ui.id as user_id, ui.name, uimg.embedding 
                FROM user_info ui
                JOIN user_images uimg ON ui.id = uimg.user_id
                WHERE uimg.is_primary = TRUE OR uimg.image_id IN (
                    SELECT MAX(image_id) FROM user_images GROUP BY user_id
                )
                """
                db_results = self.db.fetch_all(query)
                for r in db_results:
                    if r.get('embedding'):
                        r['embedding'] = json.loads(r['embedding']) if isinstance(r['embedding'], str) else r['embedding']
                        results.append(r)
                        seen_user_ids.add(str(r.get('user_id')))
            except Exception:
                pass

        # Merge local profiles
        local_profiles = self._load_local_profiles()
        profiles_updated = False
        for p in local_profiles:
            uid = p.get('id')
            uname = p.get('name')
            if str(uid) in seen_user_ids:
                continue
            
            embs = p.get('embeddings', [])
            if embs:
                for emb in embs:
                    results.append({'user_id': uid, 'name': uname, 'embedding': emb})
                seen_user_ids.add(str(uid))
            else:
                photo_path = p.get('photo_path')
                if photo_path and os.path.exists(photo_path):
                    try:
                        import face_recognition
                        loaded_img = face_recognition.load_image_file(photo_path)
                        encs = face_recognition.face_encodings(loaded_img)
                        if encs:
                            emb = encs[0].tolist()
                            p.setdefault('embeddings', []).append(emb)
                            results.append({'user_id': uid, 'name': uname, 'embedding': emb})
                            seen_user_ids.add(str(uid))
                            profiles_updated = True
                    except Exception:
                        pass
        if profiles_updated:
            self._save_local_profiles(local_profiles)

        return results

    def log_conversation(self, user_id, speaker, message, intent=None, confidence=None):
        """Log conversation message into MySQL and offline JSON log"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.db and self.db.is_connected:
            try:
                query = """
                INSERT INTO conversation_log (user_id, speaker, message, intent, confidence)
                VALUES (%s, %s, %s, %s, %s)
                """
                self.db.execute_query(query, (user_id, speaker, message, intent, confidence))
            except Exception:
                pass

        # Offline fallback log
        try:
            log_file = os.path.join(os.path.dirname(self.local_file), 'conversation_logs.json')
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            logs.append({
                'log_id': len(logs) + 1,
                'user_id': user_id,
                'speaker': speaker,
                'message': message,
                'intent': intent or '--',
                'confidence': float(confidence or 0.0),
                'timestamp': now_str
            })
            if len(logs) > 200:
                logs = logs[-200:]
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
        except Exception:
            pass
