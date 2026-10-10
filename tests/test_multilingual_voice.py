"""
Unit Tests: Multilingual Voice & Language Manager
Verifies language detection, age parsing, localized templates, and TTS voice mapping.
"""
import unittest
from voice.language_manager import LanguageManager
from voice.tts import TextToSpeech


class TestMultilingualVoice(unittest.TestCase):

    def test_language_detection(self):
        # English
        self.assertEqual(LanguageManager.detect_language("Hello, how are you today?"), "en")
        self.assertEqual(LanguageManager.detect_language("What is your name?"), "en")
        
        # Devanagari Hindi
        self.assertEqual(LanguageManager.detect_language("नमस्ते, आप कैसे हैं?"), "hi")
        self.assertEqual(LanguageManager.detect_language("मेरा नाम राहुल है।"), "hi")

        # Hinglish (Romanized Hindi)
        self.assertEqual(LanguageManager.detect_language("Mera profile bana do please"), "hinglish")
        self.assertEqual(LanguageManager.detect_language("Aapka kya haal hai"), "hinglish")
        self.assertEqual(LanguageManager.detect_language("Meri age pachees saal hai"), "hinglish")

    def test_age_parsing(self):
        # Digits
        self.assertEqual(LanguageManager.parse_age("I am 25 years old"), 25)
        self.assertEqual(LanguageManager.parse_age("Meri age 30 hai"), 30)

        # English words
        self.assertEqual(LanguageManager.parse_age("I am twenty five"), 25)
        self.assertEqual(LanguageManager.parse_age("Thirty two years"), 32)

        # Hindi / Hinglish words
        self.assertEqual(LanguageManager.parse_age("Meri umar pachees saal hai"), 25)
        self.assertEqual(LanguageManager.parse_age("Chaubees saal"), 24)
        self.assertEqual(LanguageManager.parse_age("Sattaees"), 27)
        self.assertEqual(LanguageManager.parse_age("पच्चीस साल"), 25)

    def test_localized_phrases(self):
        en_phrase = LanguageManager.get_phrase('ask_name', lang='en')
        self.assertIn("full name", en_phrase)

        hi_phrase = LanguageManager.get_phrase('ask_name', lang='hi')
        self.assertIn("नाम", hi_phrase)

        hinglish_phrase = LanguageManager.get_phrase('ask_name', lang='hinglish')
        self.assertIn("naam", hinglish_phrase)

    def test_tts_voice_detection(self):
        tts = TextToSpeech()
        # On macOS, verify Lekha or native Hindi voice is registered
        if tts.hindi_voice_id:
            self.assertIn("lekha", tts.hindi_voice_id.lower())
        self.assertIsNotNone(tts.english_voice_id)


if __name__ == '__main__':
    unittest.main()
