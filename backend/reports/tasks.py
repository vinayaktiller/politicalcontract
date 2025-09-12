import logging
from celery import shared_task
from django.utils import timezone
from datetime import date, timedelta
from django.core.management import call_command
from celery.exceptions import MaxRetriesExceededError
from reports.models import CountryDailyReport, CountryMonthlyReport, CountryWeeklyReport
from dateutil.relativedelta import relativedelta

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

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_weekly_report(self):
    try:
        # Get last week's dates (Monday to Sunday)
        today = date.today()
        last_week_start = today - timedelta(days=today.weekday() + 7)
        last_week_end = last_week_start + timedelta(days=6)
        
        # Check if weekly report already exists for this period
        if CountryWeeklyReport.objects.filter(
            week_start_date=last_week_start,
            week_last_date=last_week_end
        ).exists():
            logger.info(f"Weekly report for {last_week_start} to {last_week_end} already exists. Skipping.")
            return True
        
        # Call the weekly report generation command
        call_command(
            'generate_weekly_reports',
            start_date=last_week_start.isoformat(),
            end_date=last_week_start.isoformat()  # Only process one week
        )
        logger.info(f"Successfully generated weekly report for {last_week_start} to {last_week_end}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {str(e)}", exc_info=True)
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.critical("Max retries exceeded for weekly report generation")
        return False
    
    # reports/tasks.py (add this to your existing tasks.py)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_monthly_report(self):
    try:
        # Get last month's dates
        today = date.today()
        last_month = today - relativedelta(months=1)
        month_start = date(last_month.year, last_month.month, 1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        
        # Check if monthly report already exists for this period
        if CountryMonthlyReport.objects.filter(
            last_date=month_end,
            month=last_month.month,
            year=last_month.year
        ).exists():
            logger.info(f"Monthly report for {last_month.year}-{last_month.month:02d} already exists. Skipping.")
            return True
        
        # Call the monthly report generation command
        call_command(
            'generate_monthly_reports',
            start_date=month_start.isoformat(),
            end_date=month_start.isoformat()  # Only process one month
        )
        logger.info(f"Successfully generated monthly report for {last_month.year}-{last_month.month:02d}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate monthly report: {str(e)}", exc_info=True)
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.critical("Max retries exceeded for monthly report generation")
        return False
    
