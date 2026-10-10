"""
Unit Tests: Multilingual Entity Extractor
Verifies entity parsing across English, Hindi, and Hinglish utterances.
"""
import unittest
from ai.entity_extractor import EntityExtractor


class TestEntityExtractor(unittest.TestCase):

    def test_extract_name(self):
        self.assertEqual(EntityExtractor.extract_name("My name is Rahul Sharma"), "Rahul Sharma")
        self.assertEqual(EntityExtractor.extract_name("Mera naam Amit Patel hai"), "Amit Patel")
        self.assertEqual(EntityExtractor.extract_name("I am Sophia Loren"), "Sophia Loren")
        self.assertEqual(EntityExtractor.extract_name("Actually change my name to Rajesh"), "Rajesh")

    def test_extract_age(self):
        self.assertEqual(EntityExtractor.extract_age("I am 25 years old"), "25")
        self.assertEqual(EntityExtractor.extract_age("twenty eight"), "28")
        self.assertEqual(EntityExtractor.extract_age("Meri umar pachees saal hai"), "25")
        self.assertEqual(EntityExtractor.extract_age("chaubees"), "24")

    def test_extract_city(self):
        self.assertEqual(EntityExtractor.extract_city("I live in New York"), "New York")
        self.assertEqual(EntityExtractor.extract_city("Main Pune me rehta hoon"), "Pune")
        self.assertEqual(EntityExtractor.extract_city("from Bangalore"), "Bangalore")

    def test_extract_profession(self):
        self.assertEqual(EntityExtractor.extract_profession("I work as a Data Scientist"), "Data Scientist")
        self.assertEqual(EntityExtractor.extract_profession("Mai Software Developer hu"), "Software Developer")
        self.assertEqual(EntityExtractor.extract_profession("student at MIT"), "Student At Mit")

    def test_extract_email_and_phone(self):
        self.assertEqual(EntityExtractor.extract_email("my email is test@example.com"), "test@example.com")
        self.assertEqual(EntityExtractor.extract_email("contact me at rahul at gmail dot com"), "rahul@gmail.com")
        self.assertEqual(EntityExtractor.extract_phone("phone number is 9876543210"), "9876543210")
        self.assertEqual(EntityExtractor.extract_phone("+91-98765-43210"), "919876543210")


if __name__ == '__main__':
    unittest.main()
