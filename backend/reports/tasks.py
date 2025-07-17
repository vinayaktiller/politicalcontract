import logging
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
from django.core.management import call_command
from celery.exceptions import MaxRetriesExceededError
from reports.models import CountryDailyReport

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_daily_report(self):
    try:
        # Get yesterday's date
        yesterday = date.today() - timedelta(days=1)
        
        # Check if report already exists
        if CountryDailyReport.objects.filter(date=yesterday).exists():
            logger.info(f"Daily report for {yesterday} already exists. Skipping.")
            return True
        
        # Call the report generation command for only yesterday
        call_command(
            'generate_daily_reports', 
            start_date=yesterday.isoformat(),
            end_date=yesterday.isoformat()
        )
        logger.info(f"Successfully generated daily report for {yesterday}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate daily report: {str(e)}", exc_info=True)
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.critical("Max retries exceeded for daily report generation")
        return False