"""
Registration Agent & State Machine
Coordinates interactive multilingual voice-guided profile registration:
- Natural conversation in English, Hindi, and Hinglish
- Step-by-step state machine with 11 explicit states
- Structured answer extraction via EntityExtractor
- In-flight field corrections ("Actually my age is 26", "Change my name to Amit")
- Skipping optional fields ("skip", "chhor do")
- Graceful cancellation ("cancel", "stop", "rok do")
- Final user confirmation before persistent save into MySQL and offline backup
- Multi-turn registration session persistence into MySQL registration_sessions table
"""
import enum
import json
import uuid
import time
from typing import Dict, Any, Optional, Tuple, Callable

from ai.brain import AIBrain
from ai.entity_extractor import EntityExtractor
from voice.language_manager import LanguageManager
from services.profile_service import ProfileService


class RegistrationState(enum.Enum):
    IDLE = "idle"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_AGE = "collecting_age"
    COLLECTING_ADDRESS = "collecting_address"
    COLLECTING_CITY = "collecting_address"
    COLLECTING_JOB = "collecting_job"
    COLLECTING_PROFESSION = "collecting_job"
    COLLECTING_OPTIONAL_DETAILS = "collecting_optional_details"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SAVING = "saving"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class RegistrationAgent:
    """Manages the 11-state registration lifecycle and multilingual dialogue"""

    def __init__(self, brain: Optional[AIBrain] = None, profile_service: Optional[ProfileService] = None, status_callback: Optional[Callable[[RegistrationState, Dict[str, Any], str], None]] = None, collect_optional: bool = False):
        self.brain = brain or AIBrain()
        self.profile_service = profile_service or ProfileService()
        self.status_callback = status_callback
        self.collect_optional = collect_optional
        
        self.session_id: Optional[str] = None
        self.state = RegistrationState.IDLE
        self.current_lang = 'en'
        self.profile_data: Dict[str, Any] = {
            'name': '',
            'age': '',
            'address': '',
            'job': '',
            'email': '',
            'phone': '',
            'gender': 'Not specified',
            'preferred_language': 'en',
            'photo_path': '',
            'consent': 'Yes'
        }
        self.attempt_counts: Dict[str, int] = {}

    def is_active(self) -> bool:
        """Check if registration flow is currently active"""
        return self.state not in (
            RegistrationState.IDLE,
            RegistrationState.COMPLETED,
            RegistrationState.CANCELLED,
            RegistrationState.ERROR
        )

    def _notify(self, message: str):
        """Notify UI / callback of state and message"""
        if self.status_callback:
            try:
                self.status_callback(self.state, dict(self.profile_data), message)
            except Exception as e:
                print(f"⚠ Registration status callback error: {e}")

    def _persist_session(self):
        """Persist session state into MySQL registration_sessions table"""
        if not self.session_id:
            return
        try:
            status_map = {
                RegistrationState.IDLE: 'in_progress',
                RegistrationState.COLLECTING_NAME: 'in_progress',
                RegistrationState.COLLECTING_AGE: 'in_progress',
                RegistrationState.COLLECTING_CITY: 'in_progress',
                RegistrationState.COLLECTING_PROFESSION: 'in_progress',
                RegistrationState.COLLECTING_OPTIONAL_DETAILS: 'in_progress',
                RegistrationState.AWAITING_CONFIRMATION: 'in_progress',
                RegistrationState.SAVING: 'in_progress',
                RegistrationState.COMPLETED: 'completed',
                RegistrationState.CANCELLED: 'cancelled',
                RegistrationState.ERROR: 'error'
            }
            status_val = status_map.get(self.state, 'in_progress')
            data_json = json.dumps(self.profile_data)
            is_confirmed = (self.state == RegistrationState.COMPLETED)

            db = getattr(self.profile_service.user_store, 'db', None)
            if db and db.is_connected:
                query = """
                INSERT INTO registration_sessions (session_id, language, current_state, collected_data, is_confirmed, status, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    language=VALUES(language),
                    current_state=VALUES(current_state),
                    collected_data=VALUES(collected_data),
                    is_confirmed=VALUES(is_confirmed),
                    status=VALUES(status),
                    updated_at=NOW()
                """
                db.execute_query(query, (self.session_id, self.current_lang, self.state.value, data_json, is_confirmed, status_val))
        except Exception as e:
            # Session persistence is non-blocking
            pass

    def start_flow(self, initial_lang: str = 'en', detected_gender: str = 'Not specified', detected_age: Optional[int] = None) -> Tuple[str, str]:
        """
        Start registration state machine.
        Returns: (spoken_prompt, text_prompt)
        """
        self.session_id = str(uuid.uuid4())
        self.current_lang = initial_lang
        self.profile_data = {
            'name': '',
            'age': str(detected_age) if detected_age else '',
            'address': '',
            'job': '',
            'email': '',
            'phone': '',
            'gender': detected_gender or 'Not specified',
            'preferred_language': initial_lang,
            'photo_path': '',
            'consent': 'Yes'
        }
        self.attempt_counts = {
            'name': 0, 'age': 0, 'address': 0, 'job': 0, 'optional': 0, 'confirmation': 0
        }
        self.state = RegistrationState.COLLECTING_NAME

        prompt = LanguageManager.get_phrase('ask_name', lang=self.current_lang)
        self._persist_session()
        self._notify(prompt)
        return prompt, prompt

    def process_step(self, user_input: str, current_frame=None) -> Tuple[str, bool]:
        """
        Process user speech input in the current state.
        
        Returns:
            tuple: (robot_response, is_flow_finished)
        """
        if not user_input or not user_input.strip():
            return self._handle_empty_input()

        clean_input = user_input.strip()
        detected_lang = LanguageManager.detect_language(clean_input)
        if detected_lang != 'en' or self.current_lang == 'en':
            self.current_lang = detected_lang
            self.profile_data['preferred_language'] = detected_lang

        # 1. Check for cancellation request at any point
        if self.brain.detect_cancellation(clean_input):
            self.state = RegistrationState.CANCELLED
            self._persist_session()
            msg = LanguageManager.get_phrase('cancelled', lang=self.current_lang)
            self._notify(msg)
            return msg, True

        # 2. Check for in-flight corrections ("Actually my age is 26", "Change my name to...")
        field_to_correct, new_value = self.brain.detect_correction(clean_input, require_keyword=True)
        if field_to_correct and new_value:
            self.profile_data[field_to_correct] = new_value
            self._persist_session()
            ack = LanguageManager.get_phrase('field_updated', lang=self.current_lang, field=field_to_correct, value=new_value)
            
            # If we were already confirming, re-prompt confirmation
            if self.state == RegistrationState.AWAITING_CONFIRMATION:
                confirm_prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
                return f"{ack} {confirm_prompt}", False
            else:
                self._notify(ack)
                resume_prompt = self._get_current_state_prompt()
                return f"{ack}. {resume_prompt}", False

        # 3. Check for skipping optional field
        if self.brain.detect_skip(clean_input):
            return self._handle_skip()

        # 4. State-specific processing
        if self.state == RegistrationState.COLLECTING_NAME:
            return self._handle_collecting_name(clean_input)

        elif self.state == RegistrationState.COLLECTING_AGE:
            return self._handle_collecting_age(clean_input)

        elif self.state in (RegistrationState.COLLECTING_CITY, RegistrationState.COLLECTING_ADDRESS):
            return self._handle_collecting_city(clean_input)

        elif self.state in (RegistrationState.COLLECTING_PROFESSION, RegistrationState.COLLECTING_JOB):
            return self._handle_collecting_profession(clean_input)

        elif self.state == RegistrationState.COLLECTING_OPTIONAL_DETAILS:
            return self._handle_collecting_optional(clean_input)

        elif self.state == RegistrationState.AWAITING_CONFIRMATION:
            return self._handle_confirmation(clean_input, current_frame=current_frame)

        elif self.state == RegistrationState.ERROR:
            return self._handle_error_recovery(clean_input)

        return "I am not sure how to proceed.", False

    def _handle_collecting_name(self, text: str) -> Tuple[str, bool]:
        name = EntityExtractor.extract_name(text) or self.brain.extract_full_name(text)
        if name and len(name.split()) >= 1 and name.lower() not in ['no', 'skip', 'cancel']:
            self.profile_data['name'] = name
            self.state = RegistrationState.COLLECTING_AGE
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_age', lang=self.current_lang, name=name)
            self._notify(prompt)
            return prompt, False

        self.attempt_counts['name'] = self.attempt_counts.get('name', 0) + 1
        if self.attempt_counts['name'] >= 3:
            self.profile_data['name'] = text.title()
            self.state = RegistrationState.COLLECTING_AGE
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_age', lang=self.current_lang, name=self.profile_data['name'])
            return prompt, False

        reask = LanguageManager.get_phrase('reask_name', lang=self.current_lang)
        self._notify(reask)
        return reask, False

    def _handle_collecting_age(self, text: str) -> Tuple[str, bool]:
        age = EntityExtractor.extract_age(text) or self.brain.extract_age(text)
        if age:
            self.profile_data['age'] = str(age)
            self.state = RegistrationState.COLLECTING_CITY
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_address', lang=self.current_lang)
            self._notify(prompt)
            return prompt, False

        self.attempt_counts['age'] = self.attempt_counts.get('age', 0) + 1
        if self.attempt_counts['age'] >= 3:
            if not self.profile_data['age']:
                self.profile_data['age'] = "25"
            self.state = RegistrationState.COLLECTING_CITY
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_address', lang=self.current_lang)
            return prompt, False

        reask = LanguageManager.get_phrase('reask_age', lang=self.current_lang, name=self.profile_data['name'])
        self._notify(reask)
        return reask, False

    def _handle_collecting_city(self, text: str) -> Tuple[str, bool]:
        city = EntityExtractor.extract_city(text) or self.brain.extract_address(text)
        if city and len(city) >= 2:
            self.profile_data['address'] = city
            self.state = RegistrationState.COLLECTING_PROFESSION
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_job', lang=self.current_lang)
            self._notify(prompt)
            return prompt, False

        self.attempt_counts['address'] = self.attempt_counts.get('address', 0) + 1
        if self.attempt_counts['address'] >= 2:
            self.profile_data['address'] = text.title() if text else "Not specified"
            self.state = RegistrationState.COLLECTING_PROFESSION
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_job', lang=self.current_lang)
            return prompt, False

        reask = LanguageManager.get_phrase('reask_address', lang=self.current_lang)
        self._notify(reask)
        return reask, False

    def _handle_collecting_profession(self, text: str) -> Tuple[str, bool]:
        job = EntityExtractor.extract_profession(text) or self.brain.extract_job_or_college(text) or text.title()
        if job and len(job) >= 2:
            self.profile_data['job'] = job
        else:
            self.profile_data['job'] = "Not specified"

        if self.collect_optional:
            self.state = RegistrationState.COLLECTING_OPTIONAL_DETAILS
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_optional', lang=self.current_lang)
            self._notify(prompt)
            return prompt, False
        else:
            self.state = RegistrationState.AWAITING_CONFIRMATION
            self._persist_session()
            prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
            self._notify(prompt)
            return prompt, False

    def _handle_collecting_optional(self, text: str) -> Tuple[str, bool]:
        email = EntityExtractor.extract_email(text)
        phone = EntityExtractor.extract_phone(text)

        if email:
            self.profile_data['email'] = email
        if phone:
            self.profile_data['phone'] = phone

        self.state = RegistrationState.AWAITING_CONFIRMATION
        self._persist_session()
        prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
        self._notify(prompt)
        return prompt, False

    def _handle_confirmation(self, text: str, current_frame=None) -> Tuple[str, bool]:
        is_yes, is_no, _ = self.brain.detect_confirmation(text)

        if is_yes:
            # User confirmed! Save profile
            self.state = RegistrationState.SAVING
            self._persist_session()
            self._notify("Saving confirmed profile to database...")

            try:
                saved = self.profile_service.save_profile(self.profile_data, frame=current_frame)
                self.state = RegistrationState.COMPLETED
                self._persist_session()
                success_msg = LanguageManager.get_phrase('save_success', lang=self.current_lang, name=self.profile_data['name'])
                self._notify(success_msg)
                return success_msg, True
            except Exception as e:
                print(f"⚠ Save profile error: {e}")
                self.state = RegistrationState.ERROR
                self._persist_session()
                err_msg = LanguageManager.get_phrase('save_error', lang=self.current_lang)
                return err_msg, True

        elif is_no:
            # User wants to correct or cancel
            correction_prompt = LanguageManager.get_phrase('ask_correction', lang=self.current_lang)
            self._notify(correction_prompt)
            return correction_prompt, False

        # If user provided a correction directly during confirmation
        field_to_correct, new_value = self.brain.detect_correction(text)
        if field_to_correct and new_value:
            self.profile_data[field_to_correct] = new_value
            self._persist_session()
            ack = LanguageManager.get_phrase('field_updated', lang=self.current_lang, field=field_to_correct, value=new_value)
            confirm_prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
            return f"{ack} {confirm_prompt}", False

        # Re-ask confirmation
        prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
        return prompt, False

    def _handle_error_recovery(self, text: str) -> Tuple[str, bool]:
        """Handle recovery when an error occurs during flow"""
        is_yes, is_no, _ = self.brain.detect_confirmation(text)
        if is_no or self.brain.detect_cancellation(text):
            self.state = RegistrationState.CANCELLED
            self._persist_session()
            return LanguageManager.get_phrase('cancelled', lang=self.current_lang), True
        
        # Retry confirmation
        self.state = RegistrationState.AWAITING_CONFIRMATION
        self._persist_session()
        prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
        return prompt, False

    def _handle_skip(self) -> Tuple[str, bool]:
        ack = LanguageManager.get_phrase('skip_field', lang=self.current_lang)

        if self.state in (RegistrationState.COLLECTING_CITY, RegistrationState.COLLECTING_ADDRESS):
            self.profile_data['address'] = "Not specified"
            self.state = RegistrationState.COLLECTING_PROFESSION
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_job', lang=self.current_lang)
            return f"{ack} {prompt}", False

        elif self.state in (RegistrationState.COLLECTING_PROFESSION, RegistrationState.COLLECTING_JOB):
            self.profile_data['job'] = "Not specified"
            self.state = RegistrationState.COLLECTING_OPTIONAL_DETAILS
            self._persist_session()
            prompt = LanguageManager.get_phrase('ask_optional', lang=self.current_lang)
            return f"{ack} {prompt}", False

        elif self.state == RegistrationState.COLLECTING_OPTIONAL_DETAILS:
            self.state = RegistrationState.AWAITING_CONFIRMATION
            self._persist_session()
            prompt = LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
            return f"{ack} {prompt}", False

        # Cannot skip mandatory name or age
        reask = self._get_current_state_prompt()
        return f"{reask}", False

    def _handle_empty_input(self) -> Tuple[str, bool]:
        reask = self._get_current_state_prompt()
        return reask, False

    def _get_current_state_prompt(self) -> str:
        if self.state == RegistrationState.COLLECTING_NAME:
            return LanguageManager.get_phrase('ask_name', lang=self.current_lang)
        elif self.state == RegistrationState.COLLECTING_AGE:
            return LanguageManager.get_phrase('ask_age', lang=self.current_lang, name=self.profile_data['name'] or 'there')
        elif self.state in (RegistrationState.COLLECTING_CITY, RegistrationState.COLLECTING_ADDRESS):
            return LanguageManager.get_phrase('ask_address', lang=self.current_lang)
        elif self.state in (RegistrationState.COLLECTING_PROFESSION, RegistrationState.COLLECTING_JOB):
            return LanguageManager.get_phrase('ask_job', lang=self.current_lang)
        elif self.state == RegistrationState.COLLECTING_OPTIONAL_DETAILS:
            return LanguageManager.get_phrase('ask_optional', lang=self.current_lang)
        elif self.state == RegistrationState.AWAITING_CONFIRMATION:
            return LanguageManager.get_phrase('confirm_spoken', lang=self.current_lang, **self.profile_data)
        elif self.state == RegistrationState.ERROR:
            return LanguageManager.get_phrase('error_state', lang=self.current_lang)
        return "Please continue."
