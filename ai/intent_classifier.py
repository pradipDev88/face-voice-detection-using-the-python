"""
Intent Classifier Module
Classifies multilingual user intent across English, Hindi, and Hinglish
using a hybrid approach: deterministic rule triggers + TF-IDF Multinomial Naive Bayes.
"""
import re
from typing import Tuple, Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


class IntentClassifier:
    """Classifies user intent from natural multilingual speech or text"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, sublinear_tf=True, ngram_range=(1, 2))
        self.classifier = MultinomialNB()
        
        self.training_data = {
            'create_profile': [
                'create my profile', 'create profile', 'make my profile', 'register me',
                'register my profile', 'fill form', 'setup my profile', 'sign me up',
                'mera profile bana do', 'profile banao', 'naya profile banao',
                'form bharna hai', 'mera registration karo', 'mujhe register karo',
                'profile banana hai', 'mera khata banao', 'meri details save karo',
                'quiero crear mi perfil', 'can you register me',
                'मेरा प्रोफाइल बनाओ', 'नया प्रोफाइल रजिस्टर करो', 'फॉर्म भरो', 'खाता बनाओ'
            ],
            'profile_lookup': [
                'who am i', 'check my profile', 'lookup my profile', 'show my profile',
                'show my details', 'do you know me', 'search profile', 'my profile',
                'view profile', 'main kaun hoon', 'mera profile dikhao',
                'meri details check karo', 'kya tum mujhe jaante ho', 'mera profile check karo',
                'मैं कौन हूँ', 'मेरा प्रोफाइल दिखाओ', 'मेरी जानकारी देखो'
            ],
            'consent_yes': [
                'yes', 'yeah', 'yep', 'yup', 'sure', 'okay', 'ok', 'correct', 'right',
                'agree', 'proceed', 'save it', 'confirm', 'haan', 'ha', 'haanji',
                'sahi hai', 'bilkul', 'theek hai', 'chalega', 'pakka', 'save kar do',
                'हाँ', 'हाँजी', 'सही है', 'बिलकुल', 'ठीक है', 'आगे बढ़ो', 'सेव करो'
            ],
            'consent_no': [
                'no', 'nope', 'nah', 'not now', 'maybe later', 'dont save', 'cancel',
                'stop', 'wrong', 'incorrect', 'nevermind', 'nahi', 'na', 'galat hai',
                'rok do', 'band karo', 'mat save karo', 'nahi chahiye', 'ruk jao',
                'नहीं', 'मत करो', 'गलत है', 'रद्द करो', 'रोको', 'बंद करो'
            ],
            'greeting': [
                'hello', 'hi', 'hey', 'good morning', 'good evening', 'namaste',
                'namaskar', 'pranam', 'how are you', 'whats up', 'kaise ho',
                'kya haal hai', 'नमस्ते', 'नमस्कार', 'प्रणाम', 'आप कैसे हैं'
            ],
            'info_request': [
                'who are you', 'what is your name', 'tell me about yourself',
                'what can you do', 'help', 'features', 'tum kaun ho', 'aap kaun hain',
                'तुम कौन हो', 'आप कौन हैं', 'अपने बारे में बताओ'
            ],
            'goodbye': [
                'bye', 'goodbye', 'see you', 'take care', 'alvida', 'phir milenge',
                'chalta hoon', 'bye bye', 'अलविदा', 'फिर मिलेंगे'
            ],
            'thanks': [
                'thank you', 'thanks', 'appreciate it', 'grateful', 'dhanyawad',
                'shukriya', 'bahut shukriya', 'धन्यवाद', 'शुक्रिया'
            ]
        }
        
        self._train()

    def _train(self):
        texts = []
        labels = []
        for intent, examples in self.training_data.items():
            texts.extend(examples)
            labels.extend([intent] * len(examples))
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify intent from text with high-confidence fast path.
        Returns: (intent_name, confidence)
        """
        if not text or not text.strip():
            return ('unknown', 0.0)

        clean = text.lower().strip()

        # Fast path triggers for profile creation
        create_triggers = [
            'create my profile', 'create profile', 'make my profile', 'register me',
            'register my profile', 'fill form', 'setup my profile', 'sign me up',
            'mera profile bana do', 'profile banao', 'naya profile banao',
            'form bharna hai', 'mera registration karo', 'mujhe register karo',
            'profile banana hai', 'quiero crear mi perfil', 'मेरा प्रोफाइल'
        ]
        if any(trig in clean for trig in create_triggers):
            return ('create_profile', 0.98)

        # Fast path triggers for profile lookup
        lookup_triggers = [
            'who am i', 'check my profile', 'lookup my profile', 'show my profile',
            'do you know me', 'search profile', 'my profile', 'main kaun hoon',
            'mera profile dikhao', 'meri details check karo', 'kya tum mujhe jaante ho'
        ]
        if any(trig in clean for trig in lookup_triggers):
            return ('profile_lookup', 0.98)

        # Fast path triggers for cancellation
        cancel_triggers = ['cancel', 'stop', 'rok do', 'band karo', 'ruk jao', 'रद्द करो', 'रोको']
        if any(trig == clean or f" {trig}" in clean or f"{trig} " in clean for trig in cancel_triggers):
            return ('consent_no', 0.95)

        # Naive Bayes fallback
        try:
            X = self.vectorizer.transform([clean])
            intent = self.classifier.predict(X)[0]
            if hasattr(self.classifier, 'predict_proba'):
                proba = self.classifier.predict_proba(X)[0]
                conf = float(max(proba))
            else:
                conf = 0.8
            return (intent, conf)
        except Exception:
            return ('unknown', 0.0)
