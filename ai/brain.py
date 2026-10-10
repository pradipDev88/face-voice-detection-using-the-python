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
from voice.language_manager import LanguageManager

class AIBrain:
    """Supervised ML for intent classification and conversation understanding"""
    
    def __init__(self, model_type='naive_bayes'):
        """
        Initialize AI Brain
        
        Args:
            model_type: 'naive_bayes', 'svm', or 'neural'
        """
        self.model_type = model_type
        self.vectorizer = TfidfVectorizer(max_features=1000, sublinear_tf=True, ngram_range=(1, 2))
        self.intent_classifier = None
        self.confirmation_classifier = None
        
        # Training data for multilingual intent classification
        self.intent_training_data = {
            'greeting': [
                'hello', 'hi', 'hey', 'good morning', 'good evening', 'good afternoon',
                'namaste', 'namaskar', 'pranam', 'how are you', 'whats up', 'yo',
                'kaise ho', 'kya haal hai', 'kaisa chal raha hai', 'hello mr beast',
                'नमस्ते', 'नमस्कार', 'प्रणाम', 'आप कैसे हैं', 'क्या हाल है'
            ],
            'info_request': [
                'who are you', 'what is your name', 'tell me about yourself',
                'what can you do', 'help', 'what are your features', 'who made you',
                'tum kaun ho', 'aap kaun hain', 'kya kar sakte ho', 'apne baare me batao',
                'तुम कौन हो', 'आप कौन हैं', 'अपने बारे में बताओ', 'क्या कर सकते हो'
            ],
            'consent_yes': [
                'yes', 'yeah', 'sure', 'okay', 'ok', 'fine', 'alright',
                'go ahead', 'proceed', 'i agree', 'correct', 'right', 'yep', 'yup',
                'save it', 'confirm', 'save karo', 'haan', 'ha', 'haanji', 'sahi hai',
                'bilkul', 'theek hai', 'chalega', 'pakka', 'kar do save', 'yes please',
                'हाँ', 'हाँजी', 'सही है', 'बिलकुल', 'ठीक है', 'आगे बढ़ो', 'सेव करो'
            ],
            'consent_no': [
                'no', 'nope', 'nah', 'not now', 'maybe later', 'i dont want',
                'dont save', 'cancel', 'stop', 'wrong', 'incorrect', 'nevermind',
                'nahi', 'na', 'galat hai', 'rok do', 'band karo', 'mat save karo',
                'nahi chahiye', 'ruk jao', 'cancel karo', 'no thanks',
                'नहीं', 'मत करो', 'गलत है', 'रद्द करो', 'रोको', 'बंद करो'
            ],
            'provide_name': [
                'my name is', 'i am', 'call me', 'this is', 'name is',
                'mera naam hai', 'mera naam', 'main hoon', 'mujhe kehte hain',
                'मेरा नाम है', 'मैं हूँ'
            ],
            'provide_job': [
                'i work at', 'i study at', 'i am a student', 'i am working',
                'my job is', 'my college is', 'i go to', 'i am software engineer',
                'mai kaam karta hoon', 'mai student hu', 'mera kaam hai',
                'मैं काम करता हूँ', 'मैं छात्र हूँ'
            ],
            'create_profile': [
                'i want to create my profile', 'i want create my profile',
                'create my profile', 'create profile', 'make my profile',
                'create a profile', 'new profile', 'register me',
                'register my profile', 'setup my profile', 'fill form',
                'profile create', 'create account', 'register account',
                'i want to register', 'i want to make my profile', 'sign me up',
                'mera profile bana do', 'profile banao', 'naya profile banao',
                'form bharna hai', 'mera registration karo', 'mujhe register karo',
                'mera khata banao', 'meri details save karo', 'profile banana hai',
                'मेरा प्रोफाइल बनाओ', 'नया प्रोफाइल रजिस्टर करो', 'फॉर्म भरो',
                'रजिस्ट्रेशन शुरू करो', 'खाता बनाओ', 'मेरी जानकारी सेव करो'
            ],
            'profile_lookup': [
                'who am i', 'check my profile', 'lookup my profile', 'show my profile',
                'show my details', 'do you know me', 'search profile', 'my profile',
                'view profile', 'get user details', 'check user',
                'main kaun hoon', 'mera profile dikhao', 'meri details check karo',
                'kya tum mujhe jaante ho', 'mera profile check karo', 'mera data dikhao',
                'मैं कौन हूँ', 'मेरा प्रोफाइल दिखाओ', 'मेरी जानकारी देखो', 'क्या तुम मुझे जानते हो'
            ],
            'goodbye': [
                'bye', 'goodbye', 'see you', 'take care', 'later', 'exit', 'quit',
                'alvida', 'phir milenge', 'chalta hoon', 'bye bye',
                'अलविदा', 'फिर मिलेंगे', 'बाय बाय'
            ],
            'thanks': [
                'thank you', 'thanks', 'appreciate it', 'grateful', 'many thanks',
                'dhanyawad', 'shukriya', 'bahut shukriya', 'thanks yaar',
                'धन्यवाद', 'शुक्रिया', 'बहुत धन्यवाद'
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
        
        clean = text.lower().strip()

        # Direct high-confidence keyword triggers
        create_profile_triggers = [
            'create my profile', 'create profile', 'make my profile', 'register me',
            'register my profile', 'fill form', 'setup my profile', 'sign me up',
            'mera profile bana do', 'profile banao', 'naya profile banao',
            'form bharna hai', 'mera registration karo', 'mujhe register karo',
            'profile banana hai', 'mera profile', 'meri profile bana do',
            'मेरा प्रोफाइल', 'प्रोफाइल बनाओ', 'रजिस्टर करो'
        ]
        if any(trig in clean for trig in create_profile_triggers):
            return 'create_profile', 0.95

        profile_lookup_triggers = [
            'who am i', 'check my profile', 'lookup my profile', 'show my profile',
            'show my details', 'do you know me', 'search profile', 'my profile',
            'main kaun hoon', 'mera profile dikhao', 'meri details check karo',
            'kya tum mujhe jaante ho', 'mera profile check karo', 'mera data dikhao',
            'मैं कौन हूँ', 'मेरा प्रोफाइल दिखाओ'
        ]
        if any(trig in clean for trig in profile_lookup_triggers):
            return 'profile_lookup', 0.95

        cancel_triggers = ['cancel', 'stop', 'rok do', 'band karo', 'ruk jao', 'रद्द करो', 'रोको']
        if any(trig == clean or f" {trig}" in clean or f"{trig} " in clean for trig in cancel_triggers):
            return 'consent_no', 0.90

        try:
            X = self.vectorizer.transform([clean])
            intent = self.intent_classifier.predict(X)[0]
            
            if hasattr(self.intent_classifier, 'predict_proba'):
                proba = self.intent_classifier.predict_proba(X)[0]
                confidence = float(max(proba))
            else:
                confidence = 0.8
            
            return intent, confidence
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return 'unknown', 0.0
    
    def detect_confirmation(self, text):
        """
        Detect if user is confirming (yes/no) in English, Hindi, or Hinglish
        
        Args:
            text: User input text
            
        Returns:
            tuple: (is_yes, is_no, confidence)
        """
        if not text:
            return False, False, 0.0
        
        text = text.lower().strip()
        
        yes_keywords = [
            'yes', 'yeah', 'yep', 'yup', 'sure', 'okay', 'ok', 'correct', 'right', 'agree',
            'save', 'confirm', 'haan', 'ha', 'haanji', 'sahi hai', 'bilkul', 'theek hai',
            'chalega', 'pakka', 'हाँ', 'हाँजी', 'सही', 'बिलकुल', 'ठीक है'
        ]
        no_keywords = [
            'no', 'nope', 'nah', 'not', 'dont', 'wrong', 'incorrect', 'cancel', 'stop',
            'nahi', 'na', 'galat', 'rok do', 'band karo', 'mat save', 'ruk',
            'नहीं', 'मत करो', 'गलत', 'रद्द'
        ]
        
        is_yes = any(keyword == text or f" {keyword}" in text or f"{keyword} " in text for keyword in yes_keywords)
        is_no = any(keyword == text or f" {keyword}" in text or f"{keyword} " in text for keyword in no_keywords)
        
        intent, confidence = self.classify_intent(text)
        
        if intent == 'consent_yes':
            return True, False, confidence
        elif intent == 'consent_no':
            return False, True, confidence
        elif is_yes:
            return True, False, 0.8
        elif is_no:
            return False, True, 0.8
        else:
            return False, False, 0.0

    def detect_cancellation(self, text):
        """Check if user wants to cancel current flow"""
        if not text:
            return False
        clean = text.lower().strip()
        triggers = ['cancel', 'stop', 'abort', 'rok do', 'band karo', 'ruk jao', 'mat karo', 'nahi chahiye', 'exit', 'रद्द करो', 'रोको']
        return any(trig in clean for trig in triggers)

    def detect_skip(self, text):
        """Check if user wants to skip an optional step"""
        if not text:
            return False
        clean = text.lower().strip()
        triggers = ['skip', 'chhor do', 'chhod do', 'aage badho', 'leave it', 'pass', 'next', 'छोड़ दो', 'आगे बढ़ो']
        return any(trig in clean for trig in triggers)

    def detect_correction(self, text, require_keyword=True):
        """
        Check if user is making an in-flight correction
        Returns (field, value) or (None, None)
        """
        if not text:
            return None, None
        clean = text.lower().strip()
        correction_indicators = ['actually', 'correction', 'change', 'badal', 'badlo', 'galat', 'galti', 'instead', 'update', 'wrong', 'no wait']
        if require_keyword and not any(ind in clean for ind in correction_indicators):
            return None, None
        
        # Age correction
        if any(w in clean for w in ['age', 'umar', 'saal']):
            age = self.extract_age(clean)
            if age:
                return 'age', age
                
        # Name correction
        if any(w in clean for w in ['name', 'naam']):
            name_text = re.sub(r'^(?:actually\s+)?(?:change|update|badal\s+kar|badlo|set)\s+(?:my\s+|mera\s+)?(?:name|naam)\s+(?:to|kar\s+do|as|hai)?\s*', '', clean, flags=re.IGNORECASE)
            name = self.extract_full_name(name_text)
            if name:
                return 'name', name
                
        # City/Address correction
        if any(w in clean for w in ['city', 'address', 'shahar', 'pata', 'location']):
            addr_text = re.sub(r'^(?:actually\s+)?(?:change|update|badal\s+kar|badlo|set)\s+(?:my\s+|mera\s+)?(?:city|address|shahar|pata)\s+(?:to|kar\s+do|as|hai)?\s*', '', clean, flags=re.IGNORECASE)
            addr = self.extract_address(addr_text)
            if addr:
                return 'address', addr
                
        # Job correction
        if any(w in clean for w in ['job', 'work', 'kaam', 'college', 'profession', 'occupation']):
            job_text = re.sub(r'^(?:actually\s+)?(?:change|update|badal\s+kar|badlo|set)\s+(?:my\s+|mera\s+)?(?:job|work|kaam|profession)\s+(?:to|kar\s+do|as|hai)?\s*', '', clean, flags=re.IGNORECASE)
            job = self.extract_job_or_college(job_text)
            if job:
                return 'job', job
                
        return None, None
    
    def extract_name(self, text):
        """Extract first name from text"""
        return self.extract_full_name(text)
        
    def extract_full_name(self, text):
        """
        Extract full name from speech in English, Hindi, or Hinglish
        
        Args:
            text: User input text
            
        Returns:
            Extracted full name or None
        """
        if not text:
            return None
        clean = text.strip()
        intro_patterns = [
            r'^(?:my\s+name\s+is|i\s+am|call\s+me|this\s+is|name\s+is|myself|it\s+is|its)\s+',
            r'^(?:mera\s+naam\s+hai|mera\s+naam|main\s+hoon|mai\s+hu|naam\s+hai)\s+',
            r'^(?:मेरा\s+नाम\s+है|मेरा\s+नाम|मैं\s+हूँ)\s+'
        ]
        for pattern in intro_patterns:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE).strip()

        # Remove trailing Hindi/Hinglish particles
        clean = re.sub(r'\s+(?:hai|hoon|hu|ji|हूँ|है)$', '', clean, flags=re.IGNORECASE).strip()

        clean_words = re.findall(r'[\w]+', clean)
        filtered = [
            w for w in clean_words
            if w.lower() not in [
                'the', 'a', 'an', 'my', 'your', 'his', 'her', 'full', 'name',
                'mera', 'meri', 'naam', 'hai', 'hoon', 'hu', 'main', 'mai'
            ]
        ]
        if 1 <= len(filtered) <= 5:
            return " ".join(w.capitalize() for w in filtered)
        return clean.title() if clean else None

    def extract_age(self, text):
        """
        Extract age number from speech text in English, Hindi, or Hinglish
        
        Args:
            text: User input text
            
        Returns:
            Extracted age string or None
        """
        if not text:
            return None
        parsed = LanguageManager.parse_age(text)
        if parsed is not None:
            return str(parsed)
        return None

    def extract_address(self, text):
        """
        Extract address, city, or location from speech text
        
        Args:
            text: User input text
            
        Returns:
            Extracted address string or None
        """
        if not text:
            return None
        clean = text.strip()
        intro_patterns = [
            r'^(?:i\s+live\s+in|i\s+stay\s+in|my\s+address\s+is|address\s+is|from|living\s+in|at|i\s+am\s+from)\s+',
            r'^(?:mai\s+rehta\s+hu\s+in|mai\s+rehta\s+hoon|main\s+rehta\s+hoon|mera\s+shahar\s+hai|mera\s+address\s+hai|mai\s+se\s+hu|mai\s+|main\s+)\s*',
            r'^(?:मैं\s+रहता\s+हूँ|मेरा\s+शहर\s+है|मेरा\s+पता\s+है|मैं\s+)\s*'
        ]
        for pattern in intro_patterns:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE).strip()

        clean = re.sub(r'\s+(?:me\s+rehta\s+hu|me\s+rehta\s+hoon|me\s+rehti\s+hu|me\s+rehti\s+hoon|me|mein|hai|hoon|में|है)$', '', clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r'\s+(?:rehta\s+hu|rehta\s+hoon|rehti\s+hu|rehti\s+hoon)$', '', clean, flags=re.IGNORECASE).strip()
        return clean.title() if clean else None

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
        
        clean = text.strip()
        patterns = [
            r'i work at (.+)',
            r'i study at (.+)',
            r'my job is (.+)',
            r'my college is (.+)',
            r'i go to (.+)',
            r'i am a (.+)',
            r'i am an (.+)',
            r'working at (.+)',
            r'studying at (.+)',
            r'mai kaam karta hu (.+)',
            r'mera kaam hai (.+)',
            r'mai (.+) hoon',
            r'main (.+) hoon',
            r'mai (.+) hu'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean, re.IGNORECASE)
            if match:
                res = match.group(1).strip()
                res = re.sub(r'\s+(?:me|mein|hai|hoon|hu)$', '', res, flags=re.IGNORECASE).strip()
                return res.title()
        
        clean = re.sub(r'^(?:i\s+am\s+a|i\s+am\s+an|mai|main)\s+', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+(?:hoon|hu|hai)$', '', clean, flags=re.IGNORECASE).strip()
        if len(clean.split()) <= 10:
            return clean.title()
        
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
        
        # Profile creation request
        if intent == 'create_profile' or any(phrase in text_lower for phrase in [
            'create my profile', 'create profile', 'make my profile', 'new profile',
            'register me', 'fill form', 'create a profile', 'make profile', 'sign up'
        ]):
            return "Yes, let's start! Tell me first, what is your full name?"

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