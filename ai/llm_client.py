"""
LLM Client Module
Provides pluggable access to LLM backends (Ollama, OpenAI/Groq API)
with offline multilingual fallback responses.
"""
import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from voice.language_manager import LanguageManager


class LLMClient:
    """Pluggable LLM client with graceful offline fallback"""

    def __init__(self, model_name: str = "llama3", ollama_host: str = "http://localhost:11434", api_key: Optional[str] = None):
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
        self.system_prompt = (
            "You are Mr. Beast AI, a friendly, energetic, and helpful desktop voice robot companion. "
            "Respond naturally and concisely in 1-2 short sentences suitable for text-to-speech. "
            "Match the language of the user (English, Hindi, or Hinglish)."
        )

    def generate_response(self, text: str, lang: str = 'en') -> Optional[str]:
        """
        Generate conversational response for input text.
        Tries Ollama first if running, then API if configured, else returns None (allowing rule-based fallback).
        """
        if not text:
            return None

        # 1. Try Ollama if running
        ollama_response = self._call_ollama(text, lang)
        if ollama_response:
            return ollama_response

        # 2. Try OpenAI/Groq compatible API if key set
        if self.api_key:
            api_response = self._call_api(text, lang)
            if api_response:
                return api_response

        return None

    def _call_ollama(self, text: str, lang: str) -> Optional[str]:
        """Send query to local Ollama instance"""
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": f"{self.system_prompt}\nUser ({lang}): {text}\nMr. Beast:",
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 60}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data.get("response", "").strip()
        except Exception:
            # Ollama not running or timeout; silence warning
            pass
        return None

    def _call_api(self, text: str, lang: str) -> Optional[str]:
        """Send query to remote API"""
        # Standard OpenAI compatible endpoint
        api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ],
            "max_tokens": 60,
            "temperature": 0.7
        }
        try:
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return None
