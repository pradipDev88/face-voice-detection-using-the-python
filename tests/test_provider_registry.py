"""
Unit Tests: Provider Registry & Health Checks
Verifies provider initialization, default selection, switching,
and unified health check interface.
"""
import unittest
from services.provider_registry import (
    ProviderRegistry,
    get_provider_registry,
    LocalBrainProvider,
    BaseAIProvider
)


class TestProviderRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = ProviderRegistry()

    def test_default_providers_registered(self):
        self.assertIn('local_brain', self.registry.ai_providers)
        self.assertIn('ollama', self.registry.ai_providers)
        self.assertIn('groq', self.registry.ai_providers)
        self.assertIn('gemini', self.registry.ai_providers)
        self.assertIn('google', self.registry.stt_providers)
        self.assertIn('pyttsx3', self.registry.tts_providers)

    def test_get_ai_provider_fallback(self):
        # Default local brain
        provider = self.registry.get_ai_provider('local_brain')
        self.assertIsInstance(provider, LocalBrainProvider)

        # Non-existent falls back to local_brain
        unknown = self.registry.get_ai_provider('non_existent_provider')
        self.assertIsInstance(unknown, LocalBrainProvider)

    def test_local_brain_provider_methods(self):
        provider = self.registry.get_ai_provider('local_brain')
        
        # Test intent classification
        intent, conf = provider.classify_intent("create my profile")
        self.assertEqual(intent, "create_profile")

        # Test health check
        health = provider.health_check()
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['provider'], 'local_brain')

    def test_set_active_provider(self):
        success = self.registry.set_active_ai_provider('groq')
        self.assertTrue(success)
        self.assertEqual(self.registry.active_ai_provider_name, 'groq')

        # Invalid returns False
        fail = self.registry.set_active_ai_provider('invalid')
        self.assertFalse(fail)


if __name__ == '__main__':
    unittest.main()
