from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ..models.intitationreports import (
    CountryDailyReport,
    CountryWeeklyReport,
    CountryMonthlyReport
)
from .serializers import CountryReportSerializer
from datetime import datetime, date
from django.db.models import Q

class CountryReportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

def get_report_end_date(report):
    """Get the ending date reference for sorting"""
    if isinstance(report, CountryDailyReport):
        return report.date
    elif isinstance(report, CountryWeeklyReport):
        return report.week_last_date
    elif isinstance(report, CountryMonthlyReport):
        return report.last_date

class CountryReportListView(APIView):
    pagination_class = CountryReportPagination
    
    def get(self, request):
        report_type = request.query_params.get('report_type', 'all')
        
        # Create base query sets
        reports = []
        
        if report_type in ['all', 'daily']:
            for report in CountryDailyReport.objects.all():
                reports.append((get_report_end_date(report), report))
        
        if report_type in ['all', 'weekly']:
            for report in CountryWeeklyReport.objects.all():
                reports.append((get_report_end_date(report), report))
        
        if report_type in ['all', 'monthly']:
            for report in CountryMonthlyReport.objects.all():
                reports.append((get_report_end_date(report), report))
        
        # Sort by end date (most recent first)
        reports.sort(key=lambda x: x[0], reverse=True)
        
        # Extract just the report objects
        sorted_reports = [report for _, report in reports]
        
        # Paginate results
        paginator = self.pagination_class()
        paginated_reports = paginator.paginate_queryset(sorted_reports, request)
        
        # Serialize data
        serializer = CountryReportSerializer(paginated_reports, many=True)
        return paginator.get_paginated_response(serializer.data)

class LatestCountryReportsView(APIView):
    def get(self, request):
        # Get all reports with their end dates
        all_reports = []
        
        for report in CountryDailyReport.objects.all():
            all_reports.append((get_report_end_date(report), report))
        for report in CountryWeeklyReport.objects.all():
            all_reports.append((get_report_end_date(report), report))
        for report in CountryMonthlyReport.objects.all():
            all_reports.append((get_report_end_date(report), report))
        
        # Sort by end date (most recent first)
        all_reports.sort(key=lambda x: x[0], reverse=True)
        
        # Get top 4 most recent reports
        top_reports = [report for _, report in all_reports[:4]]
        
        # Serialize data
        serializer = CountryReportSerializer(top_reports, many=True)
        return Response(serializer.data)