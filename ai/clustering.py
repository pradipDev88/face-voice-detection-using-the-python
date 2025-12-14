"""
AI Clustering - Unsupervised Learning Module
Analyzes user behavior patterns using KMeans clustering
"""
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
import os

class UserClustering:
    """Unsupervised ML for user behavior analysis"""
    
    def __init__(self, n_clusters=5):
        """
        Initialize clustering
        
        Args:
            n_clusters: Number of user behavior clusters
        """
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Cluster descriptions
        self.cluster_profiles = {
            0: {'name': 'Quick Visitor', 'tone': 'brief', 'detail_level': 'low'},
            1: {'name': 'Engaged User', 'tone': 'friendly', 'detail_level': 'medium'},
            2: {'name': 'Curious Explorer', 'tone': 'detailed', 'detail_level': 'high'},
            3: {'name': 'Regular User', 'tone': 'casual', 'detail_level': 'medium'},
            4: {'name': 'Power User', 'tone': 'professional', 'detail_level': 'high'}
        }
        
        print(f"✓ User clustering initialized ({n_clusters} clusters)")
    
    def extract_features(self, user_data):
        """
        Extract features from user data for clustering
        
        Args:
            user_data: Dict or list of dicts with user behavior data
            
        Returns:
            numpy array of features
        """
        if isinstance(user_data, dict):
            user_data = [user_data]
        
        features = []
        
        for user in user_data:
            feature_vector = [
                user.get('avg_conv_length', 0),
                user.get('avg_time_spent', 0),
                user.get('avg_speaking_speed', 0),
                user.get('total_confirmations', 0),
                user.get('total_happy', 0),
                user.get('total_neutral', 0),
                user.get('total_sad', 0),
                user.get('conversation_count', 0)
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_clusters(self, user_behaviors):
        """
        Train clustering model on user behaviors
        
        Args:
            user_behaviors: List of user behavior dicts from database
        """
        if len(user_behaviors) < self.n_clusters:
            print(f"⚠ Not enough data for clustering (need at least {self.n_clusters} users)")
            return False
        
        try:
            # Extract features
            X = self.extract_features(user_behaviors)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train KMeans
            self.kmeans.fit(X_scaled)
            self.is_trained = True
            
            print(f"✓ Clustering trained on {len(user_behaviors)} users")
            return True
            
        except Exception as e:
            print(f"Error training clusters: {e}")
            return False
    
    def predict_cluster(self, user_data):
        """
        Predict cluster for a user
        
        Args:
            user_data: Dict with user behavior data
            
        Returns:
            tuple: (cluster_id, cluster_profile)
        """
        if not self.is_trained:
            print("⚠ Clustering model not trained yet")
            return 1, self.cluster_profiles[1]  # Default to 'Engaged User'
        
        try:
            # Extract features
            X = self.extract_features(user_data)
            
            # Scale
            X_scaled = self.scaler.transform(X)
            
            # Predict
            cluster_id = self.kmeans.predict(X_scaled)[0]
            
            # Get profile
            profile = self.cluster_profiles.get(cluster_id, self.cluster_profiles[1])
            
            return cluster_id, profile
            
        except Exception as e:
            print(f"Error predicting cluster: {e}")
            return 1, self.cluster_profiles[1]
    
    def get_cluster_profile(self, cluster_id):
        """Get profile for a cluster"""
        return self.cluster_profiles.get(cluster_id, self.cluster_profiles[1])
    
    def analyze_user_type(self, user_data):
        """
        Analyze user type and provide recommendations
        
        Args:
            user_data: Dict with user behavior data
            
        Returns:
            Dict with analysis results
        """
        cluster_id, profile = self.predict_cluster(user_data)
        
        # Analyze patterns
        avg_conv_length = user_data.get('avg_conv_length', 0)
        avg_time_spent = user_data.get('avg_time_spent', 0)
        
        analysis = {
            'cluster_id': cluster_id,
            'cluster_name': profile['name'],
            'recommended_tone': profile['tone'],
            'detail_level': profile['detail_level'],
            'is_quick_user': avg_conv_length < 5,
            'is_engaged': avg_time_spent > 60,
            'response_style': self._get_response_style(profile)
        }
        
        return analysis
    
    def _get_response_style(self, profile):
        """Get recommended response style based on profile"""
        styles = {
            'brief': 'Keep responses short and to the point',
            'friendly': 'Use warm, conversational language',
            'detailed': 'Provide comprehensive explanations',
            'casual': 'Use relaxed, informal tone',
            'professional': 'Use formal, precise language'
        }
        return styles.get(profile['tone'], 'Use balanced, friendly tone')
    
    def get_personalized_greeting(self, cluster_id):
        """Get personalized greeting based on cluster"""
        greetings = {
            0: "Hi! Quick question?",  # Quick Visitor
            1: "Hello! How can I help you today?",  # Engaged User
            2: "Welcome! I'd love to tell you more about myself!",  # Curious Explorer
            3: "Hey there! Good to see you again!",  # Regular User
            4: "Greetings! What would you like to know?"  # Power User
        }
        return greetings.get(cluster_id, "Hello! How can I assist you?")
    
    def should_provide_details(self, cluster_id):
        """Check if should provide detailed information"""
        profile = self.get_cluster_profile(cluster_id)
        return profile['detail_level'] in ['medium', 'high']
    
    def save_model(self, path='models/clustering_model.pkl'):
        """Save clustering model"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                pickle.dump({
                    'kmeans': self.kmeans,
                    'scaler': self.scaler,
                    'n_clusters': self.n_clusters,
                    'is_trained': self.is_trained
                }, f)
            print(f"✓ Clustering model saved to {path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self, path='models/clustering_model.pkl'):
        """Load clustering model"""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.kmeans = data['kmeans']
                self.scaler = data['scaler']
                self.n_clusters = data['n_clusters']
                self.is_trained = data['is_trained']
            print(f"✓ Clustering model loaded from {path}")
            return True
        except Exception as e:
            print(f"⚠ Could not load model: {e}")
            return False
