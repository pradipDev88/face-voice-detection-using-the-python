"""
AI Brain - Supervised Learning Module
Handles intent classification, confirmation detection, and conversation understanding
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
import pickle
import os
import re

class AIBrain:
    """Supervised ML for intent classification and conversation understanding"""
    
    def __init__(self, model_type='naive_bayes'):
        """
        Initialize AI Brain
        
        Args:
            model_type: 'naive_bayes', 'svm', or 'neural'
        """
        self.model_type = model_type
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.intent_classifier = None
        self.confirmation_classifier = None
        
        # Training data for intent classification
        self.intent_training_data = {
            'greeting': [
                'hello', 'hi', 'hey', 'good morning', 'good evening',
                'namaste', 'how are you', 'whats up', 'yo'
            ],
            'info_request': [
                'who are you', 'what is your name', 'tell me about yourself',
                'what can you do', 'help', 'what are your features'
            ],
            'consent_yes': [
                'yes', 'yeah', 'sure', 'okay', 'ok', 'fine', 'alright',
                'go ahead', 'proceed', 'i agree', 'correct', 'right', 'yep', 'yup'
            ],
            'consent_no': [
                'no', 'nope', 'nah', 'not now', 'maybe later', 'i dont want',
                'dont save', 'cancel', 'stop', 'wrong', 'incorrect'
            ],
            'provide_name': [
                'my name is', 'i am', 'call me', 'this is', 'name is'
            ],
            'provide_job': [
                'i work at', 'i study at', 'i am a student', 'i am working',
                'my job is', 'my college is', 'i go to'
            ],
            'goodbye': [
                'bye', 'goodbye', 'see you', 'take care', 'later', 'exit', 'quit'
            ],
            'thanks': [
                'thank you', 'thanks', 'appreciate it', 'grateful'
            ]
        }
        
        # Train models
        self.train_intent_classifier()
        
        print(f"✓ AI Brain initialized (model: {model_type})")
    
    def train_intent_classifier(self):
        """Train intent classification model"""
        # Prepare training data
        texts = []
        labels = []
        
        for intent, examples in self.intent_training_data.items():
            texts.extend(examples)
            labels.extend([intent] * len(examples))
        
        # Vectorize
        X = self.vectorizer.fit_transform(texts)
        
        # Train model
        if self.model_type == 'naive_bayes':
            self.intent_classifier = MultinomialNB()
        elif self.model_type == 'svm':
            self.intent_classifier = SVC(kernel='linear', probability=True)
        else:
            self.intent_classifier = MultinomialNB()  # Default
        
        self.intent_classifier.fit(X, labels)
        print("✓ Intent classifier trained")
    
    def classify_intent(self, text):
        """
        Classify user intent from text
        
        Args:
            text: User input text
            
        Returns:
            tuple: (intent, confidence)
        """
        if not text:
            return 'unknown', 0.0
        
        try:
            # Preprocess
            text = text.lower().strip()
            
            # Vectorize
            X = self.vectorizer.transform([text])
            
            # Predict
            intent = self.intent_classifier.predict(X)[0]
            
            # Get confidence
            if hasattr(self.intent_classifier, 'predict_proba'):
                proba = self.intent_classifier.predict_proba(X)[0]
                confidence = max(proba)
            else:
                confidence = 0.8  # Default confidence
            
            return intent, confidence
            
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return 'unknown', 0.0
    
    def detect_confirmation(self, text):
        """
        Detect if user is confirming (yes/no)
        
        Args:
            text: User input text
            
        Returns:
            tuple: (is_yes, is_no, confidence)
        """
        if not text:
            return False, False, 0.0
        
        text = text.lower().strip()
        
        # Check for explicit yes/no
        yes_keywords = ['yes', 'yeah', 'yep', 'yup', 'sure', 'okay', 'ok', 'correct', 'right', 'agree']
        no_keywords = ['no', 'nope', 'nah', 'not', 'dont', 'wrong', 'incorrect', 'cancel']
        
        is_yes = any(keyword in text for keyword in yes_keywords)
        is_no = any(keyword in text for keyword in no_keywords)
        
        # Use intent classifier for better accuracy
        intent, confidence = self.classify_intent(text)
        
        if intent == 'consent_yes':
            return True, False, confidence
        elif intent == 'consent_no':
            return False, True, confidence
        elif is_yes:
            return True, False, 0.7
        elif is_no:
            return False, True, 0.7
        else:
            return False, False, 0.0
    
    def extract_name(self, text):
        """
        Extract name from text
        
        Args:
            text: User input text
            
        Returns:
            Extracted name or None
        """
        if not text:
            return None
        
        text = text.lower().strip()
        
        # Patterns for name extraction
        patterns = [
            r'my name is (\w+)',
            r'i am (\w+)',
            r'call me (\w+)',
            r'this is (\w+)',
            r'name is (\w+)',
            r'^(\w+)$'  # Single word
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).capitalize()
                # Filter out common words
                if name.lower() not in ['the', 'a', 'an', 'my', 'your', 'his', 'her']:
                    return name
        
        return None
    
    def extract_job_or_college(self, text):
        """
        Extract job or college information
        
        Args:
            text: User input text
            
        Returns:
            Extracted info or None
        """
        if not text:
            return None
        
        text = text.strip()
        
        # Patterns for extraction
        patterns = [
            r'i work at (.+)',
            r'i study at (.+)',
            r'my job is (.+)',
            r'my college is (.+)',
            r'i go to (.+)',
            r'i am a (.+)',
            r'working at (.+)',
            r'studying at (.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, return the whole text if it's reasonable
        if len(text.split()) <= 10:
            return text
        
        return None
    
    def is_greeting(self, text):
        """Check if text is a greeting"""
        intent, confidence = self.classify_intent(text)
        return intent == 'greeting' and confidence > 0.5
    
    def is_goodbye(self, text):
        """Check if text is a goodbye"""
        intent, confidence = self.classify_intent(text)
        return intent == 'goodbye' and confidence > 0.5
    
    def is_thanks(self, text):
        """Check if text is thanks"""
        intent, confidence = self.classify_intent(text)
        return intent == 'thanks' and confidence > 0.5
    
    def save_model(self, path='models/ai_brain.pkl'):
        """Save trained model"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'classifier': self.intent_classifier,
                    'model_type': self.model_type
                }, f)
            print(f"✓ Model saved to {path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self, path='models/ai_brain.pkl'):
        """Load trained model"""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.vectorizer = data['vectorizer']
                self.intent_classifier = data['classifier']
                self.model_type = data['model_type']
            print(f"✓ Model loaded from {path}")
            return True
        except Exception as e:
            print(f"⚠ Could not load model: {e}")
            return False

class ConversationBrain:
    """Mr. Beast personality conversation brain"""
    
    def __init__(self):
        """Initialize conversation brain with Mr. Beast personality"""
        self.ai_brain = AIBrain()
        print("✓ Mr. Beast Conversation Brain initialized")
    
    def generate_response(self, user_input):
        """
        Generate Mr. Beast style response to any user input
        
        Args:
            user_input: What the user said
            
        Returns:
            str: Mr. Beast style response
        """
        if not user_input or not user_input.strip():
            return "Hey! I didn't catch that. What's up?"
        
        # Process with AI brain
        intent, confidence = self.ai_brain.classify_intent(user_input)
        text_lower = user_input.lower()
        
        # Import here to avoid circular imports
        import random
        from datetime import datetime
        
        # Mr. Beast style responses based on intent and keywords
        
        # Greetings
        if intent == 'greeting' or any(word in text_lower for word in ['hello', 'hi', 'hey']):
            responses = [
                "Hey! What's going on?",
                "Yo! How can I help you today?",
                "What's up! I'm pumped to chat with you!",
                "Hey there! Ready for something awesome?",
                "Sup! What do you want to talk about?"
            ]
            return random.choice(responses)
        
        # Identity questions
        if intent == 'info_request' or any(word in text_lower for word in ['name', 'who are you']):
            responses = [
                "I'm Mr. Beast! The most energetic AI you'll ever meet!",
                "Mr. Beast here! Ready to help you with anything!",
                "I'm Mr. Beast, your friendly AI assistant!",
                "The name's Mr. Beast! What can I do for you?"
            ]
            return random.choice(responses)
        
        # Capability questions
        if any(word in text_lower for word in ['what can you do', 'help', 'assist']):
            responses = [
                "I can chat about anything! Ask me questions, tell me jokes, or just talk!",
                "Dude, I can help with tons of stuff! What do you need?",
                "I'm here to chat and help! What's on your mind?",
                "I can answer questions, tell jokes, or just have a fun conversation!"
            ]
            return random.choice(responses)
        
        # Time questions
        if any(word in text_lower for word in ['time', 'what time']):
            current_time = datetime.now().strftime("%I:%M %p")
            return f"It's {current_time} right now!"
        
        # Date questions
        if any(word in text_lower for word in ['date', 'day', 'today']):
            current_date = datetime.now().strftime("%B %d, %Y")
            return f"Today is {current_date}!"
        
        # Joke requests
        if any(word in text_lower for word in ['joke', 'funny', 'laugh']):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "What do you call a fake noodle? An impasta!",
                "Why don't skeletons fight each other? They don't have the guts!",
                "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
                "Why did the scarecrow win an award? He was outstanding in his field!"
            ]
            return random.choice(jokes)
        
        # Weather (fake response since no API)
        if any(word in text_lower for word in ['weather', 'temperature', 'hot', 'cold']):
            return "I don't have weather data, but I hope it's awesome outside!"
        
        # Compliments
        if any(word in text_lower for word in ['awesome', 'cool', 'great', 'amazing', 'good']):
            responses = [
                "Thanks! You're pretty awesome too!",
                "Right? Everything's better when it's awesome!",
                "You know it! Let's keep this energy going!",
                "Absolutely! What else is on your mind?"
            ]
            return random.choice(responses)
        
        # Gratitude
        if intent == 'thanks' or any(word in text_lower for word in ['thank', 'thanks']):
            responses = [
                "No problem! Happy to help!",
                "You got it! What else can I do?",
                "Anytime! That's what I'm here for!",
                "You're welcome! Keep the questions coming!"
            ]
            return random.choice(responses)
        
        # Sad/negative emotions
        if any(word in text_lower for word in ['sad', 'bad', 'terrible', 'awful', 'down']):
            responses = [
                "Hey, don't worry! Things will get better!",
                "I'm here if you want to talk about it!",
                "That's tough, but you've got this!",
                "Want to talk about something fun instead?"
            ]
            return random.choice(responses)
        
        # Questions (general)
        if '?' in user_input or any(word in text_lower for word in ['what', 'how', 'why', 'when', 'where']):
            responses = [
                "That's a great question! I'm still learning, but I'll do my best!",
                "Interesting question! What do you think?",
                "Hmm, that's something to think about! Tell me more!",
                "Good question! I'd love to hear your thoughts on that!"
            ]
            return random.choice(responses)
        
        # Yes responses
        if intent == 'consent_yes':
            responses = [
                "Awesome! What's next?",
                "Sweet! Let's keep going!",
                "Perfect! What else?",
                "Yes! I love the enthusiasm!"
            ]
            return random.choice(responses)
        
        # No responses
        if intent == 'consent_no':
            responses = [
                "No worries! What would you like to do instead?",
                "That's cool! What else is on your mind?",
                "All good! Anything else you want to talk about?",
                "No problem! What should we chat about?"
            ]
            return random.choice(responses)
        
        # Default conversational responses
        responses = [
            "That's interesting! Tell me more!",
            "Cool! What else is going on?",
            "I hear you! What do you think about that?",
            "Nice! Anything else on your mind?",
            "Awesome! What else would you like to talk about?",
            "That's pretty cool! What's next?",
            "I get it! What else can we chat about?",
            "Interesting! Keep going!"
        ]
        
        return random.choice(responses)