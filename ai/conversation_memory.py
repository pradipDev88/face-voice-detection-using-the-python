"""
Conversation Memory Module
Maintains bounded, privacy-preserving multi-turn conversation context.
Does not retain unlimited personal transcripts by default.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationMemory:
    """Bounded multi-turn memory buffer with privacy controls"""

    def __init__(self, max_turns: int = 10, store_transcripts: bool = False):
        self.max_turns = max_turns
        self.store_transcripts = store_transcripts
        self.buffer: List[Dict[str, Any]] = []

    def add_turn(self, speaker: str, message: str, lang: str = 'en', intent: Optional[str] = None):
        """Add a single conversational utterance to bounded memory"""
        if not message:
            return

        entry = {
            'speaker': speaker,
            'message': message.strip(),
            'language': lang,
            'intent': intent,
            'timestamp': datetime.now().isoformat()
        }

        self.buffer.append(entry)
        if len(self.buffer) > self.max_turns:
            self.buffer.pop(0)

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent conversation turns"""
        if limit is not None:
            return self.buffer[-limit:]
        return list(self.buffer)

    def to_prompt_context(self, max_recent: int = 4) -> str:
        """Format bounded history into LLM dialogue context"""
        recent = self.buffer[-max_recent:]
        lines = []
        for turn in recent:
            lines.append(f"{turn['speaker']}: {turn['message']}")
        return "\n".join(lines)

    def clear(self):
        """Clear memory buffer immediately"""
        self.buffer.clear()
