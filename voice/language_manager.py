"""
Language Manager Module
Provides language detection, localization, and phrase templates
for English, Hindi, and Hinglish.
"""
import re
from typing import Dict, Any, Optional, Tuple


class LanguageManager:
    """Manages language detection, locales, voices, and localized responses"""

    # Common Hinglish words (Latin script representing Hindi)
    HINGLISH_KEYWORDS = {
        'mera', 'meri', 'mere', 'tera', 'teri', 'aap', 'aapka', 'aapki', 'aapke',
        'kya', 'kyun', 'kahan', 'kaise', 'kab', 'kaun', 'hai', 'hain', 'ho', 'hoon',
        'naam', 'umar', 'saal', 'shahar', 'pata', 'kaam', 'padhai', 'karo', 'karna',
        'banao', 'bana', 'banaiye', 'do', 'dijiye', 'save', 'likho', 'bharo',
        'theek', 'sahi', 'galat', 'badlo', 'badal', 'haan', 'ha', 'nahi', 'na',
        'namaste', 'namaskar', 'pranam', 'shukriya', 'dhanyawad', 'alvida', 'phir',
        'milenge', 'bilkul', 'zaroor', 'chhor', 'chhod', 'ruk', 'ruko', 'chalo',
        'chaliye', 'batao', 'batayein', 'bataiye', 'poora', 'accha', 'achha',
        'khata', 'jankari', 'mai', 'main', 'hum', 'tum', 'woh', 'yeh', 'kuchh',
        'bhai', 'yaar', 'dost', 'dekho', 'dikhao', 'sun', 'suno', 'bolo'
    }

    # Hindi number words in Latin / Hinglish and Devanagari
    HINDI_NUMBERS = {
        'ek': 1, 'do': 2, 'teen': 3, 'char': 4, 'paanch': 5, 'panch': 5,
        'chhah': 6, 'che': 6, 'saat': 7, 'aath': 8, 'nau': 9, 'dus': 10, 'das': 10,
        'gyarah': 11, 'barah': 12, 'terah': 13, 'chaudah': 14, 'pandrah': 15,
        'solah': 16, 'satrah': 17, 'atharah': 18, 'unnis': 19, 'bees': 20,
        'ikkees': 21, 'baees': 22, 'teis': 23, 'chaubees': 24, 'pachees': 25,
        'chhabbees': 26, 'sattaees': 27, 'atthaees': 28, 'untees': 29, 'tees': 30,
        'iktis': 31, 'battis': 32, 'tentis': 33, 'chauntis': 34, 'paintis': 35,
        'chhattis': 36, 'saintis': 37, 'adhtis': 38, 'untalis': 39, 'chalis': 40,
        'iktalis': 41, 'bayalis': 42, 'tetalis': 43, 'chawalis': 44, 'paintalis': 45,
        'chhiyalis': 46, 'saintalis': 47, 'adtalis': 48, 'unchas': 49, 'pachas': 50,
        'इक्कीस': 21, 'बाईस': 22, 'तेईस': 23, 'चौबीस': 24, 'पच्चीस': 25,
        'छब्बीस': 26, 'सत्ताईस': 27, 'अट्ठाईस': 28, 'उनतीस': 29, 'तीस': 30,
        'इकतीस': 31, 'बत्तीस': 32, 'पैंतीस': 35, 'छत्तीस': 36, 'चालीस': 40,
        'पचास': 50, 'साठ': 60, 'सत्तर': 70, 'अस्सी': 80, 'नब्बे': 90
    }

    # Standard English number words
    ENGLISH_NUMBERS = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90
    }

    # Localized templates
    PHRASES = {
        'en': {
            'greeting': "Hello! I am Mr. Beast, your AI voice assistant. How can I help you today?",
            'ask_name': "Sure, let's create your profile! First, what is your full name?",
            'reask_name': "I didn't quite catch that. Could you please tell me your full name clearly?",
            'ask_age': "Nice to meet you, {name}! What is your age?",
            'reask_age': "Please tell me your age in numbers, {name}.",
            'ask_address': "Got it! Which city or address do you currently live in?",
            'reask_address': "Could you repeat your city or address?",
            'ask_job': "Great! What is your profession or occupation, or are you studying?",
            'reask_job': "What do you do for work or college?",
            'confirm_details': (
                "Here are your details:\n"
                "• Name: {name}\n"
                "• Age: {age}\n"
                "• City/Address: {address}\n"
                "• Job/Studies: {job}\n\n"
                "Do you confirm these details are correct? Say yes or no."
            ),
            'confirm_spoken': "You said your name is {name}, age {age}, living in {address}, working as {job}. Is this information correct? Please say yes or no.",
            'save_success': "Congratulations {name}! Your profile has been successfully saved to the database.",
            'save_error': "There was an error saving your profile to the database, but it is stored in your offline backup.",
            'cancelled': "Profile registration has been cancelled.",
            'skip_field': "Skipping this field.",
            'photo_prompt': "Please look at the camera. Capturing your profile photo in three, two, one, smile!",
            'lookup_found': "I found your profile! Hello {name}, age {age}, from {address}, working as {job}.",
            'lookup_not_found': "I couldn't find a profile matching that name in the database.",
            'ask_correction': "What would you like to correct? Your name, age, city, or job?",
            'field_updated': "Updated your {field} to {value}.",
            'ask_optional': "Would you like to provide an email, phone number, or skip to finish?",
            'reask_optional': "Please say your email, phone number, or say 'skip' to proceed.",
            'error_state': "An error occurred during registration. Would you like to retry or cancel?"
        },
        'hi': {
            'greeting': "नमस्ते! मैं मिस्टर बीस्ट हूँ, आपका एआई वॉयस रोबोट। आज मैं आपकी क्या मदद करूँ?",
            'ask_name': "जी ज़रूर, चलिए आपका नया प्रोफ़ाइल बनाते हैं! पहले अपना पूरा नाम बताइए।",
            'reask_name': "माफ़ कीजिए, मैं सुन नहीं सका। कृपया अपना पूरा नाम फिर से बताइए।",
            'ask_age': "आपसे मिलकर खुशी हुई, {name}! आपकी उम्र कितनी है?",
            'reask_age': "कृपया अपनी उम्र अंकों में बताइए, {name}।",
            'ask_address': "बहुत बढ़िया! आप किस शहर या पते पर रहते हैं?",
            'reask_address': "कृपया अपना शहर या पता दोबारा बताइए।",
            'ask_job': "शानदार! आप क्या काम करते हैं, या पढ़ाई कर रहे हैं?",
            'reask_job': "आपकी नौकरी, पेशा या कॉलेज क्या है?",
            'confirm_details': (
                "आपकी जानकारी इस प्रकार है:\n"
                "• नाम: {name}\n"
                "• उम्र: {age}\n"
                "• शहर: {address}\n"
                "• पेशा: {job}\n\n"
                "क्या यह जानकारी सही है? हाँ या ना कहिए।"
            ),
            'confirm_spoken': "आपका नाम {name}, उम्र {age}, शहर {address}, और पेशा {job} है। क्या यह सही है? हाँ या ना बोलिए।",
            'save_success': "बधाई हो {name}! आपका प्रोफ़ाइल डेटाबेस में सफलतापूर्वक सुरक्षित कर लिया गया है।",
            'save_error': "डेटाबेस में सेव करने में समस्या आई, लेकिन आपका प्रोफ़ाइल ऑफलाइन बैकअप में सुरक्षित है।",
            'cancelled': "प्रोफ़ाइल पंजीकरण रद्द कर दिया गया है।",
            'skip_field': "यह जानकारी छोड़ दी गई है।",
            'photo_prompt': "कृपया कैमरे की तरफ देखिए। तीन, दो, एक, मुस्कुराइए!",
            'lookup_found': "मुझे आपका प्रोफ़ाइल मिल गया! नमस्ते {name}, उम्र {age}, {address} से, पेशा {job}।",
            'lookup_not_found': "डेटाबेस में इस नाम से कोई प्रोफ़ाइल नहीं मिला।",
            'ask_correction': "आप क्या बदलना चाहते हैं? नाम, उम्र, शहर, या पेशा?",
            'field_updated': "आपका {field} बदलकर {value} कर दिया गया है।",
            'ask_optional': "क्या आप ईमेल या फ़ोन नंबर जोड़ना चाहते हैं, या छोड़ना (skip) चाहते हैं?",
            'reask_optional': "कृपया ईमेल, फ़ोन नंबर बताइए, या 'skip' बोलिए।",
            'error_state': "पंजीकरण में त्रुटि आई। क्या आप दोबारा कोशिश करना चाहते हैं या रद्द करना चाहते हैं?"
        },
        'hinglish': {
            'greeting': "Namaste! Main Mr. Beast hoon, aapka AI voice robot. Aaj main aapki kya madad kar sakta hoon?",
            'ask_name': "Haan bilkul, chaliye aapka profile banate hain! Pehle apna poora naam batayein.",
            'reask_name': "Sorry, main theek se sun nahi paya. Please apna poora naam batayein.",
            'ask_age': "Aapse milkar achha laga, {name}! Aapki age ya umar kitni hai?",
            'reask_age': "Please apni age numbers me batayein, {name}.",
            'ask_address': "Got it! Aap kis city ya address me rehte hain?",
            'reask_address': "Please apni city ya address repeat karein.",
            'ask_job': "Great! Aap kya kaam karte hain, ya koi study kar rahe hain?",
            'reask_job': "Aapka occupation, job ya college kya hai?",
            'confirm_details': (
                "Aapki details hain:\n"
                "• Name: {name}\n"
                "• Age: {age}\n"
                "• City/Address: {address}\n"
                "• Job/Studies: {job}\n\n"
                "Kya yeh details sahi hain? Haan ya Na bolein."
            ),
            'confirm_spoken': "Aapka naam {name}, age {age}, city {address}, aur job {job} hai. Kya yeh details sahi hain? Haan ya Na bolein.",
            'save_success': "Badhaai ho {name}! Aapka profile database me successfully save ho gaya hai.",
            'save_error': "Database me save karne me issue aaya, lekin local backup me profile saved hai.",
            'cancelled': "Profile registration cancel kar diya gaya hai.",
            'skip_field': "Is field ko skip kar diya gaya hai.",
            'photo_prompt': "Camera ki taraf dekhein please. Three, two, one, smile!",
            'lookup_found': "Aapka profile mil gaya! Hello {name}, age {age}, location {address}, job {job}.",
            'lookup_not_found': "Is naam ka koi profile database me nahi mila.",
            'ask_correction': "Aap kya change karna chahte hain? Name, age, city ya job?",
            'field_updated': "Aapka {field} update karke {value} kar diya gaya hai.",
            'ask_optional': "Kya aap email ya phone number add karna chahte hain, ya skip karna chahte hain?",
            'reask_optional': "Email ya phone number batayein, ya 'skip' bolein aage badhne ke liye.",
            'error_state': "Registration me error aaya. Kya aap retry karna chahte hain ya cancel?"
        }
    }

    @classmethod
    def detect_language(cls, text: str) -> str:
        """
        Detect whether input text is English ('en'), Hindi Devanagari ('hi'),
        or Romanized Hindi ('hinglish').
        """
        if not text or not text.strip():
            return 'en'

        clean_text = text.strip()

        # 1. Check for Devanagari Unicode block (U+0900 to U+097F)
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', clean_text))
        total_letters = len(re.findall(r'[a-zA-Z\u0900-\u097F]', clean_text))
        
        if total_letters > 0 and (devanagari_chars / total_letters) > 0.2:
            return 'hi'

        # 2. Check for Hinglish vocabulary
        words = re.findall(r'[a-zA-Z]+', clean_text.lower())
        if not words:
            return 'en'

        hinglish_count = sum(1 for w in words if w in cls.HINGLISH_KEYWORDS)
        
        # High-confidence Hinglish trigger words
        strong_hinglish_triggers = {
            'mera', 'meri', 'mere', 'aapka', 'aapki', 'aapke', 'naam', 'umar',
            'banate', 'banayein', 'banao', 'bharna', 'karo', 'karna', 'kripya',
            'namaste', 'kaise', 'kya', 'haan', 'nahi', 'theek', 'shahar', 'pata'
        }
        has_strong_trigger = any(w in strong_hinglish_triggers for w in words)

        ratio = hinglish_count / len(words)
        if has_strong_trigger or ratio >= 0.25:
            return 'hinglish'

        return 'en'

    @classmethod
    def get_phrase(cls, key: str, lang: str = 'en', **kwargs) -> str:
        """Get localized phrase filled with keyword arguments"""
        lang = lang if lang in cls.PHRASES else 'en'
        lang_dict = cls.PHRASES.get(lang, cls.PHRASES['en'])
        template = lang_dict.get(key, cls.PHRASES['en'].get(key, ''))
        
        try:
            return template.format(**kwargs)
        except Exception:
            return template

    @classmethod
    def get_stt_locale(cls, lang: str) -> str:
        """Map language code to Google Speech Recognition locale"""
        if lang == 'hi':
            return 'hi-IN'
        elif lang in ('hinglish', 'en'):
            return 'en-IN'  # en-IN handles Indian English & Hinglish well
        return 'en-US'

    @classmethod
    def parse_age(cls, text: str) -> Optional[int]:
        """
        Extract numerical age from English, Hindi, or Hinglish speech
        """
        if not text:
            return None

        # 1. Direct digits
        digits = re.findall(r'\b\d{1,3}\b', text)
        if digits:
            val = int(digits[0])
            if 1 <= val <= 120:
                return val

        text_lower = text.lower().strip()

        # 2. Devanagari / Hinglish numbers
        for word, val in cls.HINDI_NUMBERS.items():
            pattern = rf'\b{re.escape(word)}\b'
            if re.search(pattern, text_lower):
                return val

        # 3. English numbers
        # Compound words like "twenty five"
        for tens_word, tens_val in [('twenty', 20), ('thirty', 30), ('forty', 40),
                                    ('fifty', 50), ('sixty', 60), ('seventy', 70),
                                    ('eighty', 80), ('ninety', 90)]:
            for ones_word, ones_val in [('one', 1), ('two', 2), ('three', 3), ('four', 4),
                                        ('five', 5), ('six', 6), ('seven', 7), ('eight', 8), ('nine', 9)]:
                combined = f"{tens_word} {ones_word}"
                if combined in text_lower or f"{tens_word}-{ones_word}" in text_lower:
                    return tens_val + ones_val

        # Single word English numbers
        for word, val in cls.ENGLISH_NUMBERS.items():
            pattern = rf'\b{re.escape(word)}\b'
            if re.search(pattern, text_lower):
                return val

        return None
