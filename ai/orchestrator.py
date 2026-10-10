"""
AI Orchestrator Module
Central conversation engine implementing the Master Architecture pipeline:
1. Multilingual Speech / Text Input
2. Language Detection (English, Hindi, Hinglish)
3. Safe Tool Routing (datetime, math, diagnostics, profile lookup/delete)
4. Intent Routing:
   - Branch A: Create Profile (Registration State Machine)
   - Branch B: Existing Profile (Profile Lookup)
   - Branch C: General Conversation & Tool Execution (Knowledge Base + LLM fallback)
5. Multi-turn Bounded Conversation Memory with Privacy Protection
6. Multilingual TTS dispatch coordination
"""
from typing import Dict, Any, Optional, Tuple, Callable
import re

from ai.brain import AIBrain
from ai.registration_agent import RegistrationAgent, RegistrationState
from ai.llm_client import LLMClient
from ai.tool_router import ToolRouter
from ai.conversation_memory import ConversationMemory
from services.profile_service import ProfileService
from services.health_service import HealthService
from voice.language_manager import LanguageManager


class AIOrchestrator:
    """Central AI conversation engine coordinating intents, tools, and stateful dialogues"""

    def __init__(
        self,
        brain: Optional[AIBrain] = None,
        profile_service: Optional[ProfileService] = None,
        llm_client: Optional[LLMClient] = None,
        tool_router: Optional[ToolRouter] = None,
        memory: Optional[ConversationMemory] = None,
        ui_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.brain = brain or AIBrain()
        self.profile_service = profile_service or ProfileService()
        self.llm_client = llm_client or LLMClient()
        self.ui_callback = ui_callback

        self.memory = memory or ConversationMemory(max_turns=10)
        self.health_service = HealthService(
            db_conn=getattr(self.profile_service.user_store, 'db', None),
            sync_manager=self.profile_service.sync_manager
        )
        self.tool_router = tool_router or ToolRouter(
            profile_service=self.profile_service,
            health_service=self.health_service
        )

        self.registration_agent = RegistrationAgent(
            brain=self.brain,
            profile_service=self.profile_service,
            status_callback=self._on_registration_status
        )

        self.current_lang = 'en'

    def _on_registration_status(self, state: RegistrationState, profile_data: Dict[str, Any], message: str):
        """Forward status to UI callback"""
        if self.ui_callback:
            try:
                self.ui_callback({
                    'type': 'registration_update',
                    'state': state.value,
                    'profile_data': profile_data,
                    'message': message,
                    'language': self.current_lang
                })
            except Exception as e:
                print(f"⚠ Orchestrator UI callback error: {e}")

    def handle_input(self, text: str, current_frame=None, current_face_data=None) -> Dict[str, Any]:
        """
        Process speech text from user and route along the architectural pipeline.
        
        Returns:
            dict containing:
                - 'response': robot response text
                - 'intent': classified intent
                - 'language': detected language ('en', 'hi', 'hinglish')
                - 'branch': 'create_profile' | 'profile_lookup' | 'tool_execution' | 'general_conversation'
                - 'is_registration_active': boolean
        """
        if not text or not text.strip():
            return {
                'response': "I didn't hear anything. Please speak or type.",
                'intent': 'unknown',
                'language': self.current_lang,
                'branch': 'general_conversation',
                'is_registration_active': self.registration_agent.is_active()
            }

        clean_text = text.strip()

        # 1. Language Detection
        self.current_lang = LanguageManager.detect_language(clean_text)

        # 2. Check if currently in registration flow
        if self.registration_agent.is_active():
            self.memory.add_turn('User', clean_text, lang=self.current_lang, intent='registration_step')
            reply, is_finished = self.registration_agent.process_step(clean_text, current_frame=current_frame)
            self.memory.add_turn('Robot', reply, lang=self.current_lang, intent='registration_step')
            return {
                'response': reply,
                'intent': 'create_profile_in_progress',
                'language': self.current_lang,
                'branch': 'create_profile',
                'is_registration_active': not is_finished
            }

        # 3. Safe Tool Routing check (fast-path triggers)
        tool_handled, tool_response = self._check_tool_execution(clean_text)
        if tool_handled:
            self.memory.add_turn('User', clean_text, lang=self.current_lang, intent='tool_execution')
            self.memory.add_turn('Robot', tool_response, lang=self.current_lang, intent='tool_execution')
            return {
                'response': tool_response,
                'intent': 'tool_execution',
                'language': self.current_lang,
                'branch': 'tool_execution',
                'is_registration_active': False
            }

        # 4. Intent Classification
        intent, confidence = self.brain.classify_intent(clean_text)

        # 5. Route according to Architecture Branches:

        # Branch 1: Create Profile
        if intent == 'create_profile':
            gender = current_face_data.get('gender', 'Not specified') if current_face_data else 'Not specified'
            age = current_face_data.get('age') if current_face_data else None
            spoken_prompt, _ = self.registration_agent.start_flow(
                initial_lang=self.current_lang,
                detected_gender=gender,
                detected_age=age
            )
            self.memory.add_turn('User', clean_text, lang=self.current_lang, intent='create_profile')
            self.memory.add_turn('Robot', spoken_prompt, lang=self.current_lang, intent='create_profile')
            return {
                'response': spoken_prompt,
                'intent': 'create_profile',
                'language': self.current_lang,
                'branch': 'create_profile',
                'is_registration_active': True
            }

        # Branch 2: Profile Lookup (Existing Profile)
        elif intent == 'profile_lookup':
            name_target = self.brain.extract_full_name(clean_text)
            found_user = self.profile_service.lookup_profile(name_query=name_target)
            
            if found_user:
                resp = LanguageManager.get_phrase(
                    'lookup_found',
                    lang=self.current_lang,
                    name=found_user.get('name', 'Friend'),
                    age=found_user.get('age', '25'),
                    address=found_user.get('address', 'Unknown'),
                    job=found_user.get('job', 'Professional')
                )
            else:
                resp = LanguageManager.get_phrase('lookup_not_found', lang=self.current_lang)

            self.memory.add_turn('User', clean_text, lang=self.current_lang, intent='profile_lookup')
            self.memory.add_turn('Robot', resp, lang=self.current_lang, intent='profile_lookup')
            return {
                'response': resp,
                'intent': 'profile_lookup',
                'language': self.current_lang,
                'branch': 'profile_lookup',
                'is_registration_active': False
            }

        # Branch 3: General Conversation
        else:
            resp = self._generate_conversational_response(clean_text, intent)
            self.memory.add_turn('User', clean_text, lang=self.current_lang, intent=intent)
            self.memory.add_turn('Robot', resp, lang=self.current_lang, intent=intent)
            return {
                'response': resp,
                'intent': intent,
                'language': self.current_lang,
                'branch': 'general_conversation',
                'is_registration_active': False
            }

    def _check_tool_execution(self, text: str) -> Tuple[bool, str]:
        """Check if input text triggers safe tool execution"""
        lower = text.lower().strip()

        # Datetime Tool
        time_triggers = ['what time', 'current time', 'what is the date', 'today\'s date', 'time kya hai', 'date kya hai', 'aaj konsa din hai', 'samay kya hai']
        if any(trig in lower for trig in time_triggers):
            res = self.tool_router.execute_tool('get_datetime')
            if res.get('success'):
                return True, res['result']

        # Math Calculation Tool
        calc_match = re.search(r'(?:calculate|what is|how much is|solve|hisab karo)\s+([\d\s\+\-\*\/\(\)\.]+)', lower)
        if calc_match:
            expr = calc_match.group(1).strip()
            res = self.tool_router.execute_tool('calculate', expression=expr)
            if res.get('success'):
                return True, res['result']

        # Diagnostics Tool
        diag_triggers = ['run diagnostics', 'check diagnostics', 'check health', 'system health', 'system check']
        if any(trig in lower for trig in diag_triggers):
            res = self.tool_router.execute_tool('run_diagnostics')
            if res.get('success'):
                diag_data = res.get('result', {})
                overall = diag_data.get('overall', 'unknown')
                db_status = diag_data.get('components', {}).get('database', {}).get('status', 'unknown')
                ai_status = diag_data.get('components', {}).get('ai_provider', {}).get('status', 'unknown')
                report = f"System Diagnostics: Overall status is {overall}. Database is {db_status}. AI provider is {ai_status}."
                return True, report

        return False, ""

    def _generate_conversational_response(self, text: str, intent: str) -> str:
        """Generate response for general chat using knowledge base or LLM fallback"""
        # 1. Standard intent responses in matching language
        if intent == 'greeting':
            return LanguageManager.get_phrase('greeting', lang=self.current_lang)
        elif intent == 'thanks':
            if self.current_lang == 'hi':
                return "आपका स्वागत है! मुझे आपकी सहायता करके खुशी हुई।"
            elif self.current_lang == 'hinglish':
                return "You're most welcome! Main hamesha aapki madad ke liye taiyar hoon."
            return "You're very welcome! Always happy to help!"
        elif intent == 'goodbye':
            if self.current_lang == 'hi':
                return "अलविदा! आपका दिन शुभ हो!"
            elif self.current_lang == 'hinglish':
                return "Alvida! Phir milenge, apna khayal rakhna!"
            return "Goodbye! Have an amazing day ahead!"
        elif intent == 'info_request':
            if self.current_lang == 'hi':
                return "मैं मिस्टर बीस्ट हूँ, आपका स्मार्ट वॉयस रोबोट। मैं चेहरे पहचान सकता हूँ और आपकी प्रोफ़ाइल रजिस्टर कर सकता हूँ।"
            elif self.current_lang == 'hinglish':
                return "Main Mr. Beast hoon, aapka smart AI robot. Main face detect kar sakta hoon aur voice se profile register kar sakta hoon!"
            return "I am Mr. Beast, an AI voice desktop robot with face recognition, age detection, and autonomous profile registration."

        # 2. Try LLM if available, passing recent conversation context
        context_prompt = self.memory.to_prompt_context(max_recent=4)
        llm_reply = self.llm_client.generate_response(text, lang=self.current_lang)
        if llm_reply:
            return llm_reply

        # 3. Fallback smart conversational reply
        if self.current_lang == 'hi':
            return "मैंने आपकी बात सुनी। अगर आप नया प्रोफ़ाइल बनाना चाहते हैं, तो कहिए 'मेरा प्रोफ़ाइल बनाओ'।"
        elif self.current_lang == 'hinglish':
            return "Maine suna! Agar aapko naya profile create karna hai, toh bas kahiye 'Mera profile bana do'!"
        return "I heard you! If you want to create a new profile, just say 'Create my profile'!"
