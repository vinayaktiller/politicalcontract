from django.urls import path
from .reportslist.views import CountryReportListView, LatestCountryReportsView
from .reportview.views import ReportDetailView
from .overallreport.views import OverallReportView

urlpatterns = [
    path('reports/list/', CountryReportListView.as_view(), name='reports-list'),
    path('reports/latest/', LatestCountryReportsView.as_view(), name='latest-reports'),
    path('reports/view/', ReportDetailView.as_view(), name='report-detail'),  # Added this line
    path('overall-report/', OverallReportView.as_view(), name='overall-report'),
]