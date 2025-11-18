# # reports/api.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from datetime import date, timedelta
# from dateutil.relativedelta import relativedelta

# from users.login.authentication import CookieJWTAuthentication
# from rest_framework.permissions import IsAuthenticated
# from users.permissions.permissions import IsSuperUser

# from .services import ReportGenerationService

# class GetPendingReportsView(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def get(self, request):
#         """Get all pending reports that need to be generated"""
#         try:
#             pending_daily = ReportGenerationService.get_pending_daily_dates()
#             pending_weekly = ReportGenerationService.get_pending_weekly_periods()
#             pending_monthly = ReportGenerationService.get_pending_monthly_periods()
            
#             response_data = {
#                 'daily': {
#                     'count': len(pending_daily),
#                     'periods': [d.isoformat() for d in pending_daily]
#                 },
#                 'weekly': {
#                     'count': len(pending_weekly),
#                     'periods': [
#                         {
#                             'week_start': p['week_start'].isoformat(),
#                             'week_end': p['week_end'].isoformat(),
#                             'week_number': p['week_number'],
#                             'year': p['year']
#                         } for p in pending_weekly
#                     ]
#                 },
#                 'monthly': {
#                     'count': len(pending_monthly),
#                     'periods': [
#                         {
#                             'month_start': p['month_start'].isoformat(),
#                             'month_end': p['month_end'].isoformat(),
#                             'month': p['month'],
#                             'year': p['year']
#                         } for p in pending_monthly
#                     ]
#                 }
#             }
            
#             return Response(response_data)
            
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class GenerateAllPendingReportsView(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def post(self, request):
#         """Generate all pending reports"""
#         try:
#             results = {}
            
#             # Generate daily reports
#             pending_daily = ReportGenerationService.get_pending_daily_dates()
#             if pending_daily:
#                 results['daily'] = ReportGenerationService.generate_daily_reports_for_dates(pending_daily)
            
#             # Generate weekly reports
#             pending_weekly = ReportGenerationService.get_pending_weekly_periods()
#             if pending_weekly:
#                 results['weekly'] = ReportGenerationService.generate_weekly_reports_for_periods(pending_weekly)
            
#             # Generate monthly reports
#             pending_monthly = ReportGenerationService.get_pending_monthly_periods()
#             if pending_monthly:
#                 results['monthly'] = ReportGenerationService.generate_monthly_reports_for_periods(pending_monthly)
            
#             # Calculate summary
#             total_success = sum(
#                 len([r for r in results[report_type] if r['status'] == 'success'])
#                 for report_type in results
#             )
#             total_error = sum(
#                 len([r for r in results[report_type] if r['status'] == 'error'])
#                 for report_type in results
#             )
            
#             response_data = {
#                 'summary': {
#                     'total_processed': total_success + total_error,
#                     'successful': total_success,
#                     'errors': total_error
#                 },
#                 'details': results
#             }
            
#             return Response(response_data)
            
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class GenerateCustomReportsView(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def post(self, request):
#         """Generate reports for custom date range"""
#         try:
#             data = request.data
            
#             start_date = date.fromisoformat(data.get('start_date'))
#             end_date = date.fromisoformat(data.get('end_date'))
#             report_types = data.get('report_types', ['daily', 'weekly', 'monthly'])
            
#             if start_date > end_date:
#                 return Response(
#                     {'error': 'Start date cannot be after end date'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             if end_date >= date.today():
#                 return Response(
#                     {'error': 'End date must be in the past'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             results = ReportGenerationService.generate_custom_range_reports(
#                 start_date, end_date, report_types
#             )
            
#             return Response(results)
            
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class GenerateSpecificPeriodReportsView(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def post(self, request):
#         """Generate reports for specific periods"""
#         try:
#             data = request.data
            
#             results = {}
            
#             # Generate specific daily reports
#             daily_dates = data.get('daily_dates', [])
#             if daily_dates:
#                 dates = [date.fromisoformat(d) for d in daily_dates]
#                 results['daily'] = ReportGenerationService.generate_daily_reports_for_dates(dates)
            
#             # Generate specific weekly reports
#             weekly_periods = data.get('weekly_periods', [])
#             if weekly_periods:
#                 results['weekly'] = ReportGenerationService.generate_weekly_reports_for_periods(weekly_periods)
            
#             # Generate specific monthly reports
#             monthly_periods = data.get('monthly_periods', [])
#             if monthly_periods:
#                 results['monthly'] = ReportGenerationService.generate_monthly_reports_for_periods(monthly_periods)
            
#             return Response(results)
            
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# class GenerateLastNDaysReportsView(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def post(self, request):
#         """Generate reports for last N days"""
#         try:
#             data = request.data
#             days = data.get('days', 7)  # Default to last 7 days
            
#             end_date = date.today() - timedelta(days=1)
#             start_date = end_date - timedelta(days=days - 1)
            
#             report_types = data.get('report_types', ['daily'])
            
#             results = ReportGenerationService.generate_custom_range_reports(
#                 start_date, end_date, report_types
#             )
            
#             response_data = {
#                 'period': {
#                     'start_date': start_date.isoformat(),
#                     'end_date': end_date.isoformat(),
#                     'days': days
#                 },
#                 'results': results
#             }
            
#             return Response(response_data)
            
#         except Exception as e:
#             return Response(
#                 {'error': str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# reports/api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from users.permissions.permissions import IsSuperUser

from .services import ReportGenerationService

class YesterdayReportStatusView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        """Get yesterday's report status"""
        try:
            status_info = ReportGenerationService.get_yesterday_status()
            return Response(status_info)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GenerateYesterdayReportView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request):
        """Generate yesterday's report"""
        try:
            result = ReportGenerationService.generate_yesterday_report()
            return Response(result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )