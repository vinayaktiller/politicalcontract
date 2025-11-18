# # reports/services.py
# from datetime import date, timedelta
# from dateutil.relativedelta import relativedelta
# from django.core.management import call_command
# from django.db import transaction
# from reports.models import (
#     CountryDailyReport, CountryWeeklyReport, CountryMonthlyReport,
#     VillageDailyReport, SubdistrictDailyReport, DistrictDailyReport, StateDailyReport
# )
# from users.models import Petitioner
# import logging

# logger = logging.getLogger(__name__)

# class ReportGenerationService:
#     @staticmethod
#     def get_pending_daily_dates():
#         """Get dates for which daily reports are missing"""
#         try:
#             # Get first user date
#             first_user = Petitioner.objects.order_by('date_joined').first()
#             if not first_user:
#                 return []
            
#             start_date = first_user.date_joined.date()
#             end_date = date.today() - timedelta(days=1)
            
#             # Get existing report dates
#             existing_dates = set(
#                 CountryDailyReport.objects.filter(
#                     date__range=[start_date, end_date]
#                 ).values_list('date', flat=True)
#             )
            
#             # Generate all dates in range
#             all_dates = []
#             current_date = start_date
#             while current_date <= end_date:
#                 all_dates.append(current_date)
#                 current_date += timedelta(days=1)
            
#             # Return missing dates
#             pending_dates = [d for d in all_dates if d not in existing_dates]
#             return sorted(pending_dates)
            
#         except Exception as e:
#             logger.error(f"Error getting pending daily dates: {str(e)}")
#             return []

#     @staticmethod
#     def get_pending_weekly_periods():
#         """Get weekly periods for which reports are missing"""
#         try:
#             first_user = Petitioner.objects.order_by('date_joined').first()
#             if not first_user:
#                 return []
            
#             first_date = first_user.date_joined.date()
#             # Start from Monday of the first user's week
#             start_date = first_date - timedelta(days=first_date.weekday())
            
#             # End at last complete week
#             today = date.today()
#             end_date = today - timedelta(days=today.weekday() + 7)
            
#             pending_periods = []
#             current_week_start = start_date
            
#             while current_week_start <= end_date:
#                 week_end = current_week_start + timedelta(days=6)
#                 week_number = current_week_start.isocalendar()[1]
#                 year = current_week_start.year
                
#                 # Check if weekly report exists
#                 exists = CountryWeeklyReport.objects.filter(
#                     week_start_date=current_week_start,
#                     week_last_date=week_end,
#                     week_number=week_number,
#                     year=year
#                 ).exists()
                
#                 if not exists:
#                     pending_periods.append({
#                         'week_start': current_week_start,
#                         'week_end': week_end,
#                         'week_number': week_number,
#                         'year': year
#                     })
                
#                 current_week_start += timedelta(days=7)
            
#             return pending_periods
            
#         except Exception as e:
#             logger.error(f"Error getting pending weekly periods: {str(e)}")
#             return []

#     @staticmethod
#     def get_pending_monthly_periods():
#         """Get monthly periods for which reports are missing"""
#         try:
#             first_user = Petitioner.objects.order_by('date_joined').first()
#             if not first_user:
#                 return []
            
#             first_date = first_user.date_joined.date()
#             start_date = date(first_date.year, first_date.month, 1)
            
#             today = date.today()
#             last_month = today - relativedelta(months=1)
#             end_date = date(last_month.year, last_month.month, 1)
            
#             pending_periods = []
#             current_month_start = start_date
            
#             while current_month_start <= end_date:
#                 month_end = (current_month_start + relativedelta(months=1)) - timedelta(days=1)
#                 month = current_month_start.month
#                 year = current_month_start.year
                
#                 # Check if monthly report exists
#                 exists = CountryMonthlyReport.objects.filter(
#                     last_date=month_end,
#                     month=month,
#                     year=year
#                 ).exists()
                
#                 if not exists:
#                     pending_periods.append({
#                         'month_start': current_month_start,
#                         'month_end': month_end,
#                         'month': month,
#                         'year': year
#                     })
                
#                 current_month_start += relativedelta(months=1)
            
#             return pending_periods
            
#         except Exception as e:
#             logger.error(f"Error getting pending monthly periods: {str(e)}")
#             return []

#     @staticmethod
#     def generate_daily_reports_for_dates(dates):
#         """Generate daily reports for specific dates"""
#         results = []
#         for report_date in dates:
#             try:
#                 with transaction.atomic():
#                     call_command(
#                         'generate_daily_reports',
#                         start_date=report_date.isoformat(),
#                         end_date=report_date.isoformat()
#                     )
#                 results.append({
#                     'date': report_date.isoformat(),
#                     'status': 'success',
#                     'message': f'Daily report generated for {report_date}'
#                 })
#             except Exception as e:
#                 results.append({
#                     'date': report_date.isoformat(),
#                     'status': 'error',
#                     'message': str(e)
#                 })
#         return results

#     @staticmethod
#     def generate_weekly_reports_for_periods(periods):
#         """Generate weekly reports for specific periods"""
#         results = []
#         for period in periods:
#             try:
#                 with transaction.atomic():
#                     call_command(
#                         'generate_weekly_reports',
#                         start_date=period['week_start'].isoformat(),
#                         end_date=period['week_start'].isoformat()
#                     )
#                 results.append({
#                     'period': f"Week {period['week_number']} ({period['week_start']} to {period['week_end']})",
#                     'status': 'success',
#                     'message': f'Weekly report generated for week {period["week_number"]}'
#                 })
#             except Exception as e:
#                 results.append({
#                     'period': f"Week {period['week_number']} ({period['week_start']} to {period['week_end']})",
#                     'status': 'error',
#                     'message': str(e)
#                 })
#         return results

#     @staticmethod
#     def generate_monthly_reports_for_periods(periods):
#         """Generate monthly reports for specific periods"""
#         results = []
#         for period in periods:
#             try:
#                 with transaction.atomic():
#                     call_command(
#                         'generate_monthly_reports',
#                         start_date=period['month_start'].isoformat(),
#                         end_date=period['month_start'].isoformat()
#                     )
#                 results.append({
#                     'period': f"{period['year']}-{period['month']:02d}",
#                     'status': 'success',
#                     'message': f'Monthly report generated for {period["year"]}-{period["month"]:02d}'
#                 })
#             except Exception as e:
#                 results.append({
#                     'period': f"{period['year']}-{period['month']:02d}",
#                     'status': 'error',
#                     'message': str(e)
#                 })
#         return results

#     @staticmethod
#     def generate_custom_range_reports(start_date, end_date, report_types):
#         """Generate reports for custom date range"""
#         results = {}
        
#         try:
#             if 'daily' in report_types:
#                 with transaction.atomic():
#                     call_command(
#                         'generate_daily_reports',
#                         start_date=start_date.isoformat(),
#                         end_date=end_date.isoformat()
#                     )
#                 results['daily'] = {
#                     'status': 'success',
#                     'message': f'Daily reports generated from {start_date} to {end_date}'
#                 }

#             if 'weekly' in report_types:
#                 with transaction.atomic():
#                     call_command(
#                         'generate_weekly_reports',
#                         start_date=start_date.isoformat(),
#                         end_date=end_date.isoformat()
#                     )
#                 results['weekly'] = {
#                     'status': 'success', 
#                     'message': f'Weekly reports generated from {start_date} to {end_date}'
#                 }

#             if 'monthly' in report_types:
#                 with transaction.atomic():
#                     call_command(
#                         'generate_monthly_reports',
#                         start_date=start_date.isoformat(),
#                         end_date=end_date.isoformat()
#                     )
#                 results['monthly'] = {
#                     'status': 'success',
#                     'message': f'Monthly reports generated from {start_date} to {end_date}'
#                 }

#         except Exception as e:
#             results['error'] = {
#                 'status': 'error',
#                 'message': str(e)
#             }
        
#         return results


# reports/services.py
from datetime import date, timedelta
from django.core.management import call_command
from django.db import transaction
from reports.models import CountryDailyReport
from users.models import Petitioner
import logging

logger = logging.getLogger(__name__)

class ReportGenerationService:
    @staticmethod
    def get_yesterday_status():
        """Check if yesterday's report exists and return status"""
        try:
            yesterday = date.today() - timedelta(days=1)
            
            # Check if yesterday's report exists
            report_exists = CountryDailyReport.objects.filter(date=yesterday).exists()
            
            return {
                'date': yesterday.isoformat(),
                'exists': report_exists,
                'message': 'Report already exists' if report_exists else 'Report pending'
            }
            
        except Exception as e:
            logger.error(f"Error checking yesterday's report: {str(e)}")
            return {
                'date': (date.today() - timedelta(days=1)).isoformat(),
                'exists': False,
                'message': f'Error: {str(e)}'
            }

    @staticmethod
    def generate_yesterday_report():
        """Generate yesterday's report if it doesn't exist"""
        try:
            yesterday = date.today() - timedelta(days=1)
            
            # Check if report already exists
            if CountryDailyReport.objects.filter(date=yesterday).exists():
                return {
                    'status': 'already_exists',
                    'message': f'Daily report for {yesterday} already exists',
                    'date': yesterday.isoformat()
                }
            
            # Generate the report
            with transaction.atomic():
                call_command(
                    'generate_daily_reports',
                    start_date=yesterday.isoformat(),
                    end_date=yesterday.isoformat()
                )
            
            # Verify it was created
            if CountryDailyReport.objects.filter(date=yesterday).exists():
                return {
                    'status': 'success',
                    'message': f'Successfully generated daily report for {yesterday}',
                    'date': yesterday.isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to generate report for {yesterday}',
                    'date': yesterday.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating yesterday's report: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error generating report: {str(e)}',
                'date': (date.today() - timedelta(days=1)).isoformat()
            }