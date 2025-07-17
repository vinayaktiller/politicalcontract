from django.apps import AppConfig
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class ActivityReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_reports'
    
    def ready(self):
        # Import signals module
        import activity_reports.signals
        logger.info(f"{self.name} signals registered")