from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..models import (
    DailyCountryActivityReport,
    WeeklyCountryActivityReport,
    MonthlyCountryActivityReport
)
from .serializers import CountryActivityReportSerializer

class CountryActivityReportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

def get_activity_report_end_date(report):
    """Get the ending date reference for sorting"""
    if isinstance(report, DailyCountryActivityReport):
        return report.date
    elif isinstance(report, WeeklyCountryActivityReport):
        return report.week_last_date
    elif isinstance(report, MonthlyCountryActivityReport):
        return report.last_date

class CountryActivityReportListView(APIView):
    pagination_class = CountryActivityReportPagination
    
    def get(self, request):
        report_type = request.query_params.get('report_type', 'all')
        
        # Create base query sets
        reports = []
        
        if report_type in ['all', 'daily']:
            for report in DailyCountryActivityReport.objects.all():
                reports.append((get_activity_report_end_date(report), report))
        
        if report_type in ['all', 'weekly']:
            for report in WeeklyCountryActivityReport.objects.all():
                reports.append((get_activity_report_end_date(report), report))
        
        if report_type in ['all', 'monthly']:
            for report in MonthlyCountryActivityReport.objects.all():
                reports.append((get_activity_report_end_date(report), report))
        
        # Sort by end date (most recent first)
        reports.sort(key=lambda x: x[0], reverse=True)
        
        # Extract just the report objects
        sorted_reports = [report for _, report in reports]
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_reports = paginator.paginate_queryset(sorted_reports, request)
        
        # Serialize data
        serializer = CountryActivityReportSerializer(paginated_reports, many=True)
        return paginator.get_paginated_response(serializer.data)

class LatestCountryActivityReportsView(APIView):
    def get(self, request):
        # Get all reports with their end dates
        all_reports = []
        
        for report in DailyCountryActivityReport.objects.all():
            all_reports.append((get_activity_report_end_date(report), report))
        for report in WeeklyCountryActivityReport.objects.all():
            all_reports.append((get_activity_report_end_date(report), report))
        for report in MonthlyCountryActivityReport.objects.all():
            all_reports.append((get_activity_report_end_date(report), report))
        
        # Sort by end date (most recent first)
        all_reports.sort(key=lambda x: x[0], reverse=True)
        
        # Get top 4 most recent reports
        top_reports = [report for _, report in all_reports[:4]]
        
        # Serialize data
        serializer = CountryActivityReportSerializer(top_reports, many=True)
        return Response(serializer.data)