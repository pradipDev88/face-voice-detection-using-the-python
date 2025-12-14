"""
Hybrid AI Brain
Combines supervised and unsupervised learning for intelligent conversation management
"""
from ai.brain import AIBrain
from ai.clustering import UserClustering

class HybridBrain:
    """Hybrid AI combining supervised intent detection with unsupervised behavior clustering"""
    
    def __init__(self):
        """Initialize hybrid brain"""
        self.supervised_brain = AIBrain(model_type='naive_bayes')
        self.unsupervised_brain = UserClustering(n_clusters=5)
        
        # Conversation state
        self.current_state = 'idle'  # idle, greeting, onboarding, confirming, chatting
        self.pending_confirmation = None
        self.user_context = {}
        
        print("✓ Hybrid AI Brain initialized")
    
    def process_user_input(self, text, user_data=None):
        """
        Process user input using both supervised and unsupervised models
        
        Args:
            text: User input text
            user_data: User behavior data for clustering
            
        Returns:
            Dict with processing results and recommended response
        """
        # Supervised: Classify intent
        intent, confidence = self.supervised_brain.classify_intent(text)
        
        # Supervised: Check for confirmation
        is_yes, is_no, conf_confidence = self.supervised_brain.detect_confirmation(text)
        
        # Unsupervised: Analyze user behavior (if data available)
        cluster_analysis = None
        if user_data:
            cluster_analysis = self.unsupervised_brain.analyze_user_type(user_data)
        
        # Combine insights
        result = {
            'text': text,
            'intent': intent,
            'confidence': confidence,
            'is_yes': is_yes,
            'is_no': is_no,
            'confirmation_confidence': conf_confidence,
            'cluster_analysis': cluster_analysis,
            'recommended_response': self._generate_response(intent, cluster_analysis),
            'should_be_detailed': cluster_analysis['detail_level'] in ['medium', 'high'] if cluster_analysis else True
        }
        
        return result
    
    def _generate_response(self, intent, cluster_analysis):
        """Generate appropriate response based on intent and cluster"""
        # Base responses
        responses = {
            'greeting': "Hello! I'm Mr. Beast, your AI assistant. How can I help you today?",
            'info_request': "I'm Mr. Beast, an AI-powered voice robot. I can recognize faces, detect age and gender, and have conversations with you!",
            'consent_yes': "Great! Thank you for your consent.",
            'consent_no': "No problem! I won't save your information.",
            'goodbye': "Goodbye! Have a great day!",
            'thanks': "You're welcome! Happy to help!",
            'unknown': "I'm not sure I understood that. Could you please rephrase?"
        }
        
        base_response = responses.get(intent, responses['unknown'])
        
        # Adjust based on cluster
        if cluster_analysis:
            tone = cluster_analysis['recommended_tone']
            
            if tone == 'brief' and len(base_response) > 50:
                # Shorten response for quick users
                base_response = base_response.split('.')[0] + '.'
            elif tone == 'detailed' and intent == 'info_request':
                # Add more details for curious users
                base_response += " I use advanced AI to analyze faces and understand conversations. Would you like to know more?"
        
        return base_response
    
    def handle_onboarding_flow(self, current_step, user_input, user_data=None):
        """
        Handle user onboarding conversation flow
        
        Args:
            current_step: Current onboarding step
            user_input: User's text input
            user_data: User behavior data
            
        Returns:
            Dict with next step and response
        """
        result = self.process_user_input(user_input, user_data)
        
        flow = {
            'ask_consent': {
                'next_step': 'ask_name' if result['is_yes'] else 'end',
                'response': "Great! What's your name?" if result['is_yes'] else "No problem! I won't save your data."
            },
            'ask_name': {
                'next_step': 'ask_job',
                'response': f"Nice to meet you! What do you do? Are you a student or working?"
            },
            'ask_job': {
                'next_step': 'confirm_save',
                'response': "Got it! Let me confirm - should I save this information?"
            },
            'confirm_save': {
                'next_step': 'complete' if result['is_yes'] else 'end',
                'response': "Perfect! Your information has been saved." if result['is_yes'] else "Okay, I won't save it."
            }
        }
        
        return flow.get(current_step, {'next_step': 'end', 'response': 'Thank you!'})
    
    def handle_recognition_flow(self, is_match, user_name, user_input):
        """
        Handle face recognition confirmation flow
        
        Args:
            is_match: Whether face matched database
            user_name: Matched user name
            user_input: User's response
            
        Returns:
            Dict with action and response
        """
        result = self.process_user_input(user_input)
        
        if is_match:
            if result['is_yes']:
                return {
                    'action': 'confirmed',
                    'response': f"Welcome back, {user_name}! How can I help you today?"
                }
            elif result['is_no']:
                return {
                    'action': 'new_user',
                    'response': "Oh, my apologies! Let me treat you as a new visitor. May I save your details?"
                }
        
        return {
            'action': 'unclear',
            'response': "I didn't quite catch that. Could you please say yes or no?"
        }
    
    def get_personalized_greeting(self, user_data):
        """Get personalized greeting based on user cluster"""
        if not user_data:
            return "Hello! I'm Mr. Beast. How can I help you?"
        
        cluster_id, profile = self.unsupervised_brain.predict_cluster(user_data)
        greeting = self.unsupervised_brain.get_personalized_greeting(cluster_id)
        
        return greeting
    
    def should_ask_for_details(self, user_data):
        """Determine if should ask for detailed information"""
        if not user_data:
            return True
        
        cluster_id, profile = self.unsupervised_brain.predict_cluster(user_data)
        return self.unsupervised_brain.should_provide_details(cluster_id)
    
    def extract_information(self, text, info_type):
        """
        Extract specific information from text
        
        Args:
            text: User input
            info_type: 'name', 'job', or 'college'
            
        Returns:
            Extracted information or None
        """
        if info_type == 'name':
            return self.supervised_brain.extract_name(text)
        elif info_type in ['job', 'college']:
            return self.supervised_brain.extract_job_or_college(text)
        return None
    
    def train_from_database(self, user_behaviors):
        """Train unsupervised model from database"""
        return self.unsupervised_brain.train_clusters(user_behaviors)
    
    def save_models(self):
        """Save both supervised and unsupervised models"""
        self.supervised_brain.save_model()
        self.unsupervised_brain.save_model()
        print("✓ Hybrid brain models saved")
    
    def load_models(self):
        """Load both supervised and unsupervised models"""
        supervised_loaded = self.supervised_brain.load_model()
        unsupervised_loaded = self.unsupervised_brain.load_model()
        
        if supervised_loaded and unsupervised_loaded:
            print("✓ Hybrid brain models loaded")
            return True
        return False
