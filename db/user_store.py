"""
User Store Module
Handles all user-related database operations
"""
from db.connection import get_db
from datetime import datetime
import json

class UserStore:
    """Manages user data in database"""
    
    def __init__(self):
        """Initialize user store"""
        self.db = get_db()
    
    def create_user(self, name, age_range, gender, college_or_job, consent='No'):
        """Create new user"""
        query = """
        INSERT INTO user_info (name, age_range, gender, college_or_job, consent, first_seen, last_seen)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        now = datetime.now()
        params = (name, age_range, gender, college_or_job, consent, now, now)
        user_id = self.db.execute_query(query, params)
        
        if user_id:
            print(f"✓ User created: {name} (ID: {user_id})")
        return user_id
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM user_info WHERE id = %s"
        return self.db.fetch_one(query, (user_id,))
    
    def get_user_by_name(self, name):
        """Get user by name"""
        query = "SELECT * FROM user_info WHERE name = %s"
        return self.db.fetch_one(query, (name,))
    
    def update_last_seen(self, user_id):
        """Update user's last seen timestamp"""
        query = "UPDATE user_info SET last_seen = %s WHERE id = %s"
        self.db.execute_query(query, (datetime.now(), user_id))
    
    def update_user_info(self, user_id, **kwargs):
        """Update user information"""
        allowed_fields = ['name', 'age_range', 'gender', 'college_or_job', 'consent', 
                         'conversation_count', 'avg_conversation_length', 'engagement_score', 'cluster_id']
        
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                params.append(value)
        
        if updates:
            query = f"UPDATE user_info SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)
            self.db.execute_query(query, tuple(params))
            print(f"✓ User {user_id} updated")
    
    def save_user_image(self, user_id, file_path, embedding, is_primary=False):
        """Save user face image and embedding"""
        query = """
        INSERT INTO user_images (user_id, file_path, embedding, is_primary)
        VALUES (%s, %s, %s, %s)
        """
        embedding_json = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
        params = (user_id, file_path, embedding_json, is_primary)
        image_id = self.db.execute_query(query, params)
        
        if image_id:
            print(f"✓ Image saved for user {user_id}")
        return image_id
    
    def get_user_embeddings(self, user_id):
        """Get all embeddings for a user"""
        query = "SELECT * FROM user_images WHERE user_id = %s"
        results = self.db.fetch_all(query, (user_id,))
        
        # Parse JSON embeddings
        for result in results:
            if result['embedding']:
                result['embedding'] = json.loads(result['embedding'])
        
        return results
    
    def get_all_embeddings(self):
        """Get all user embeddings for matching"""
        query = """
        SELECT ui.id as user_id, ui.name, uimg.embedding 
        FROM user_info ui
        JOIN user_images uimg ON ui.id = uimg.user_id
        WHERE uimg.is_primary = TRUE OR uimg.image_id IN (
            SELECT MAX(image_id) FROM user_images GROUP BY user_id
        )
        """
        results = self.db.fetch_all(query)
        
        # Parse JSON embeddings
        for result in results:
            if result['embedding']:
                result['embedding'] = json.loads(result['embedding'])
        
        return results
    
    def log_conversation(self, user_id, speaker, message, intent=None, confidence=None):
        """Log conversation message"""
        query = """
        INSERT INTO conversation_log (user_id, speaker, message, intent, confidence)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, speaker, message, intent, confidence)
        self.db.execute_query(query, params)
    
    def get_conversation_history(self, user_id, limit=50):
        """Get conversation history for user"""
        query = """
        SELECT * FROM conversation_log 
        WHERE user_id = %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        return self.db.fetch_all(query, (user_id, limit))
    
    def save_user_behavior(self, user_id, behavior_data):
        """Save user behavior data for clustering"""
        query = """
        INSERT INTO user_behavior 
        (user_id, session_date, conversation_length, time_spent_seconds, 
         speaking_speed, confirmation_count, emotion_happy_count, 
         emotion_neutral_count, emotion_sad_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            user_id,
            datetime.now().date(),
            behavior_data.get('conversation_length', 0),
            behavior_data.get('time_spent_seconds', 0),
            behavior_data.get('speaking_speed', 0.0),
            behavior_data.get('confirmation_count', 0),
            behavior_data.get('emotion_happy_count', 0),
            behavior_data.get('emotion_neutral_count', 0),
            behavior_data.get('emotion_sad_count', 0)
        )
        self.db.execute_query(query, params)
    
    def get_all_user_behaviors(self):
        """Get all user behaviors for clustering"""
        query = """
        SELECT user_id, 
               AVG(conversation_length) as avg_conv_length,
               AVG(time_spent_seconds) as avg_time_spent,
               AVG(speaking_speed) as avg_speaking_speed,
               SUM(confirmation_count) as total_confirmations,
               SUM(emotion_happy_count) as total_happy,
               SUM(emotion_neutral_count) as total_neutral,
               SUM(emotion_sad_count) as total_sad
        FROM user_behavior
        GROUP BY user_id
        """
        return self.db.fetch_all(query)
    
    def increment_conversation_count(self, user_id):
        """Increment user's conversation count"""
        query = "UPDATE user_info SET conversation_count = conversation_count + 1 WHERE id = %s"
        self.db.execute_query(query, (user_id,))
