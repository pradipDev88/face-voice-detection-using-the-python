"""
Health Service Module
Aggregates health checks from all providers, database connectivity,
camera status, and synchronization queues to report real application health.
"""
import time
from datetime import datetime
from typing import Dict, Any
from services.provider_registry import get_provider_registry
from db.connection import get_db
from db.sync_manager import SyncManager


class HealthService:
    """Aggregates and reports application and provider health metrics"""

    def __init__(self, registry=None, db=None, sync_manager=None, db_conn=None, **kwargs):
        self.registry = registry or get_provider_registry()
        self.db = db or db_conn or get_db()
        self.sync_manager = sync_manager or SyncManager()

    def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check across all sub-systems"""
        components: Dict[str, Any] = {}
        is_healthy = True
        is_degraded = False

        # 1. Database Check
        db_start = time.time()
        try:
            if self.db and self.db.is_connected():
                # Quick ping query
                self.db.fetch_one("SELECT 1")
                latency_ms = int((time.time() - db_start) * 1000)
                components['database'] = {
                    'status': 'healthy',
                    'provider': 'mysql',
                    'latency_ms': latency_ms,
                    'database': 'mr_beast_db'
                }
            else:
                is_degraded = True
                components['database'] = {
                    'status': 'offline',
                    'provider': 'mysql',
                    'message': 'Database offline. Offline local JSON backup active.'
                }
        except Exception as e:
            is_degraded = True
            components['database'] = {
                'status': 'error',
                'provider': 'mysql',
                'error': str(e)
            }

        # 2. Conversational AI Provider Check
        ai_provider = self.registry.get_ai_provider()
        ai_health = ai_provider.health_check()
        components['ai_provider'] = ai_health

        # 3. Speech-to-Text Provider Check
        stt_provider = self.registry.get_stt_provider()
        stt_health = stt_provider.health_check()
        components['speech_to_text'] = stt_health
        if stt_health.get('status') != 'healthy':
            is_degraded = True

        # 4. Text-to-Speech Provider Check
        tts_provider = self.registry.get_tts_provider()
        tts_health = tts_provider.health_check()
        components['text_to_speech'] = tts_health

        # 5. Sync Queue Check
        sync_status = self.sync_manager.get_status()
        components['sync_queue'] = sync_status

        # Overall Status determination
        overall_status = 'healthy'
        if is_degraded:
            overall_status = 'degraded'
        if not components.get('text_to_speech', {}).get('status') == 'healthy':
            overall_status = 'unhealthy'

        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': components
        }
