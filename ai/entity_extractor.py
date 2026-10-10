"""
Multilingual Entity Extractor Module
Extracts structured registration fields from natural spoken sentences:
- Name (English, Hindi, Hinglish)
- Age (digits, English words, Hindi/Hinglish numbers)
- City / Address
- Profession / Studies
- Email & Phone (optional fields)
"""
import re
from typing import Optional, Dict, Any
from voice.language_manager import LanguageManager


class EntityExtractor:
    """Extracts verified structured entities from natural multilingual text"""

    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """Extract full name (1 to 4 words) from speech text"""
        if not text or not text.strip():
            return None
        clean = text.strip()

        # Strip common sentence openers
        intro_patterns = [
            r'^(?:my\s+name\s+is|i\s+am|call\s+me|this\s+is|name\s+is|myself|it\s+is|its)\s+',
            r'^(?:mera\s+naam\s+hai|mera\s+naam|main\s+hoon|mai\s+hu|naam\s+hai)\s+',
            r'^(?:मेरा\s+नाम\s+है|मेरा\s+नाम|मैं\s+हूँ)\s+',
            r'^(?:actually\s+)?(?:change|update|badal\s+kar|badlo|set)\s+(?:my\s+|mera\s+)?(?:name|naam)\s+(?:to|kar\s+do|as|hai)?\s*'
        ]
        for pattern in intro_patterns:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE).strip()

        # Remove trailing particles
        clean = re.sub(r'\s+(?:hai|hoon|hu|ji|हूँ|है)$', '', clean, flags=re.IGNORECASE).strip()

        words = re.findall(r'[\w]+', clean)
        stop_words = {
            'the', 'a', 'an', 'my', 'your', 'his', 'her', 'full', 'name',
            'mera', 'meri', 'naam', 'hai', 'hoon', 'hu', 'main', 'mai', 'ji'
        }
        filtered = [w for w in words if w.lower() not in stop_words]

        if 1 <= len(filtered) <= 5:
            return " ".join(w.capitalize() for w in filtered)
        return clean.title() if clean else None

    @staticmethod
    def extract_age(text: str) -> Optional[str]:
        """Extract numerical age from speech text"""
        if not text or not text.strip():
            return None
        parsed = LanguageManager.parse_age(text)
        if parsed is not None:
            return str(parsed)
        return None

    @staticmethod
    def extract_city(text: str) -> Optional[str]:
        """Extract city or location from speech text"""
        if not text or not text.strip():
            return None
        clean = text.strip()

        intro_patterns = [
            r'^(?:i\s+live\s+in|i\s+stay\s+in|my\s+address\s+is|address\s+is|from|living\s+in|at|i\s+am\s+from)\s+',
            r'^(?:mai\s+rehta\s+hu\s+in|mai\s+rehta\s+hoon|main\s+rehta\s+hoon|mera\s+shahar\s+hai|mera\s+address\s+hai|mai\s+se\s+hu|mai\s+|main\s+)\s*',
            r'^(?:मैं\s+रहता\s+हूँ|मेरा\s+शहर\s+है|मेरा\s+पता\s+है|मैं\s+)\s*'
        ]
        for pattern in intro_patterns:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE).strip()

        # Strip trailing particles
        clean = re.sub(r'\s+(?:me\s+rehta\s+hu|me\s+rehta\s+hoon|me\s+rehti\s+hu|me\s+rehti\s+hoon|me|mein|hai|hoon|में|है)$', '', clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r'\s+(?:rehta\s+hu|rehta\s+hoon|rehti\s+hu|rehti\s+hoon)$', '', clean, flags=re.IGNORECASE).strip()
        return clean.title() if clean else None

    @staticmethod
    def extract_profession(text: str) -> Optional[str]:
        """Extract occupation, job, or college from speech text"""
        if not text or not text.strip():
            return None
        clean = text.strip()

        patterns = [
            r'i work as an? (.+)',
            r'i work at (.+)',
            r'i study at (.+)',
            r'my job is (.+)',
            r'my college is (.+)',
            r'i go to (.+)',
            r'i am an? (.+)',
            r'working at (.+)',
            r'studying at (.+)',
            r'mai (.+) engineer hoon',
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

        clean = re.sub(r'^(?:i\s+am\s+an?|mai|main)\s+', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+(?:hoon|hu|hai)$', '', clean, flags=re.IGNORECASE).strip()
        if len(clean.split()) <= 10:
            return clean.title()

        return None

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email address using regex"""
        if not text:
            return None
        # Handle spoken "at the rate" or "dot com"
        normalized = text.lower().replace(" at ", "@").replace(" dot ", ".").replace(" at the rate ", "@").strip()
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', normalized)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract phone number (10 to 12 digits)"""
        if not text:
            return None
        digits = re.sub(r'[^\d]', '', text)
        if 10 <= len(digits) <= 13:
            return digits
        return None
