"""
Provider Registry Module
Central service registry where Conversational AI, Speech Recognition (STT),
Text-to-Speech (TTS), and Computer Vision providers can be configured,
replaced, tested, and health-checked independently.
"""
import os
import json
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple


# ==============================================================================
# Abstract Provider Interfaces
# ==============================================================================

class BaseAIProvider(ABC):
    """Abstract interface for Conversational AI providers"""

    @abstractmethod
    def generate_response(self, text: str, lang: str = 'en', context: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        pass

    @abstractmethod
    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def classify_intent(self, text: str) -> Tuple[str, float]:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass


class BaseSTTProvider(ABC):
    """Abstract interface for Speech-to-Text providers"""

    @abstractmethod
    def transcribe_audio(self, audio_data: Any, language: str = 'auto') -> Optional[str]:
        pass

    @abstractmethod
    def detect_language(self, audio_data: Any) -> str:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass


class BaseTTSProvider(ABC):
    """Abstract interface for Text-to-Speech providers"""

    @abstractmethod
    def speak(self, text: str, lang: str = 'en', block: bool = True) -> None:
        pass

    @abstractmethod
    def stop_speaking(self) -> None:
        pass

    @abstractmethod
    def list_available_voices(self) -> List[Tuple[str, str]]:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass


# ==============================================================================
# Concrete Conversational AI Providers
# ==============================================================================

class OllamaAIProvider(BaseAIProvider):
    """Local Ollama Provider (zero-cost, private)"""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3"):
        self.host = host
        self.model = model

    def generate_response(self, text: str, lang: str = 'en', context: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        url = f"{self.host}/api/generate"
        prompt = (
            f"You are Mr. Beast AI, an energetic, friendly desktop voice assistant. "
            f"Reply in 1-2 concise spoken sentences matching the language of the user ({lang}).\n"
            f"User: {text}\nMr. Beast:"
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 50}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1.8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data.get("response", "").strip()
        except Exception:
            return None
        return None

    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def classify_intent(self, text: str) -> Tuple[str, float]:
        return ('general_conversation', 0.8)

    def health_check(self) -> Dict[str, Any]:
        start = time.time()
        url = f"{self.host}/api/tags"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                latency = int((time.time() - start) * 1000)
                if resp.status == 200:
                    return {'status': 'healthy', 'provider': 'ollama', 'latency_ms': latency, 'model': self.model}
        except Exception as e:
            return {'status': 'unavailable', 'provider': 'ollama', 'error': str(e), 'details': 'Ollama service not running locally'}
        return {'status': 'unavailable', 'provider': 'ollama'}


class GroqAIProvider(BaseAIProvider):
    """Groq Cloud API Provider (ultra-fast inference)"""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model

    def generate_response(self, text: str, lang: str = 'en', context: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        if not self.api_key:
            return None
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"You are Mr. Beast AI, a helpful voice robot. Respond concisely in 1-2 sentences matching language: {lang}."},
                {"role": "user", "content": text}
            ],
            "max_tokens": 60,
            "temperature": 0.7
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None
        return None

    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def classify_intent(self, text: str) -> Tuple[str, float]:
        return ('general_conversation', 0.8)

    def health_check(self) -> Dict[str, Any]:
        if not self.api_key:
            return {'status': 'not_configured', 'provider': 'groq', 'details': 'GROQ_API_KEY is not set'}
        return {'status': 'configured', 'provider': 'groq', 'model': self.model}


class GeminiAIProvider(BaseAIProvider):
    """Google Gemini API Provider"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model

    def generate_response(self, text: str, lang: str = 'en', context: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        if not self.api_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        prompt = f"You are Mr. Beast AI voice robot. Reply in 1-2 spoken sentences matching language ({lang}): {text}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            return None
        return None

    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def classify_intent(self, text: str) -> Tuple[str, float]:
        return ('general_conversation', 0.8)

    def health_check(self) -> Dict[str, Any]:
        if not self.api_key:
            return {'status': 'not_configured', 'provider': 'gemini', 'details': 'GEMINI_API_KEY is not set'}
        return {'status': 'configured', 'provider': 'gemini', 'model': self.model}


class LocalBrainProvider(BaseAIProvider):
    """Built-in Local Hybrid AI Brain (TF-IDF + Naive Bayes, offline)"""

    def __init__(self):
        from ai.brain import AIBrain
        self.brain = AIBrain()

    def generate_response(self, text: str, lang: str = 'en', context: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        from voice.language_manager import LanguageManager
        intent, _ = self.brain.classify_intent(text)
        if intent in ('greeting', 'thanks', 'goodbye', 'info_request'):
            return LanguageManager.get_phrase(intent, lang=lang)
        return LanguageManager.get_phrase('greeting', lang=lang)

    def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = {}
        if 'name' in schema:
            data['name'] = self.brain.extract_full_name(text)
        if 'age' in schema:
            data['age'] = self.brain.extract_age(text)
        if 'address' in schema:
            data['address'] = self.brain.extract_address(text)
        if 'job' in schema:
            data['job'] = self.brain.extract_job_or_college(text)
        return data

    def classify_intent(self, text: str) -> Tuple[str, float]:
        return self.brain.classify_intent(text)

    def health_check(self) -> Dict[str, Any]:
        return {'status': 'healthy', 'provider': 'local_brain', 'type': 'naive_bayes'}


# ==============================================================================
# Speech Recognition & Text-to-Speech Provider Implementations
# ==============================================================================

class GoogleSTTProvider(BaseSTTProvider):
    """Google Speech Recognition Provider via SpeechToText"""

    def __init__(self):
        from voice.stt import SpeechToText
        self.stt = SpeechToText()

    def transcribe_audio(self, audio_data: Any, language: str = 'auto') -> Optional[str]:
        return self.stt.listen_once(timeout=4)

    def detect_language(self, audio_data: Any) -> str:
        return getattr(self.stt, 'last_detected_language', 'en')

    def health_check(self) -> Dict[str, Any]:
        avail = getattr(self.stt, 'is_available', False)
        backend = getattr(self.stt, 'backend', 'unknown')
        return {
            'status': 'healthy' if avail else 'unavailable',
            'provider': 'google_stt',
            'backend': backend,
            'device_index': getattr(self.stt, 'sd_device_index', None)
        }


class Pyttsx3TTSProvider(BaseTTSProvider):
    """pyttsx3 Text-to-Speech Provider with Lekha/Rishi multi-voice support"""

    def __init__(self):
        from voice.tts import TextToSpeech
        self.tts = TextToSpeech()

    def speak(self, text: str, lang: str = 'en', block: bool = True) -> None:
        self.tts.speak(text, lang=lang, block=block)

    def stop_speaking(self) -> None:
        self.tts.stop()

    def list_available_voices(self) -> List[Tuple[str, str]]:
        return self.tts.get_voices()

    def health_check(self) -> Dict[str, Any]:
        return {
            'status': 'healthy',
            'provider': 'pyttsx3',
            'hindi_voice': getattr(self.tts, 'hindi_voice_id', None),
            'english_voice': getattr(self.tts, 'english_voice_id', None)
        }


# ==============================================================================
# Provider Registry Singleton
# ==============================================================================

class ProviderRegistry:
    """Central registry maintaining active AI, STT, and TTS providers"""

    def __init__(self):
        self.ai_providers: Dict[str, BaseAIProvider] = {}
        self.stt_providers: Dict[str, BaseSTTProvider] = {}
        self.tts_providers: Dict[str, BaseTTSProvider] = {}

        self.active_ai_provider_name = os.getenv("PRIMARY_AI_PROVIDER", "local_brain")
        self.active_stt_provider_name = "google"
        self.active_tts_provider_name = "pyttsx3"

        self._init_defaults()

    def _init_defaults(self):
        # Register default providers
        self.ai_providers['local_brain'] = LocalBrainProvider()
        self.ai_providers['ollama'] = OllamaAIProvider(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3")
        )
        self.ai_providers['groq'] = GroqAIProvider(
            api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        )
        self.ai_providers['gemini'] = GeminiAIProvider(
            api_key=os.getenv("GEMINI_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        )

        self.stt_providers['google'] = GoogleSTTProvider()
        self.tts_providers['pyttsx3'] = Pyttsx3TTSProvider()

    def get_ai_provider(self, name: Optional[str] = None) -> BaseAIProvider:
        target = name or self.active_ai_provider_name
        if target in self.ai_providers:
            return self.ai_providers[target]
        return self.ai_providers.get('local_brain', list(self.ai_providers.values())[0])

    def get_stt_provider(self, name: Optional[str] = None) -> BaseSTTProvider:
        target = name or self.active_stt_provider_name
        return self.stt_providers.get(target, list(self.stt_providers.values())[0])

    def get_tts_provider(self, name: Optional[str] = None) -> BaseTTSProvider:
        target = name or self.active_tts_provider_name
        return self.tts_providers.get(target, list(self.tts_providers.values())[0])

    def set_active_ai_provider(self, name: str) -> bool:
        if name in self.ai_providers:
            self.active_ai_provider_name = name
            return True
        return False


_global_registry = None

def get_provider_registry() -> ProviderRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ProviderRegistry()
    return _global_registry
