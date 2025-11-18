# # reports/manulreports/urls.py

# from django.urls import path
# from .reportslist.views import CountryReportListView, LatestCountryReportsView
# from .reportview.views import ReportDetailView
# from .overallreport.views import OverallReportView
# from .manulreports.views import (
#     GetPendingReportsView,
#     GenerateAllPendingReportsView,
#     GenerateCustomReportsView,
#     GenerateSpecificPeriodReportsView,
#     GenerateLastNDaysReportsView,
# )

# urlpatterns = [
#     path('reports/list/', CountryReportListView.as_view(), name='reports-list'),
#     path('reports/latest/', LatestCountryReportsView.as_view(), name='latest-reports'),
#     path('reports/view/', ReportDetailView.as_view(), name='report-detail'),
#     path('overall-report/', OverallReportView.as_view(), name='overall-report'),

#     path('pending/', GetPendingReportsView.as_view(), name='get-pending-reports'),
#     path('generate-all-pending/', GenerateAllPendingReportsView.as_view(), name='generate-all-pending'),
#     path('generate-custom/', GenerateCustomReportsView.as_view(), name='generate-custom-reports'),
#     path('generate-specific/', GenerateSpecificPeriodReportsView.as_view(), name='generate-specific'),
#     path('generate-last-n-days/', GenerateLastNDaysReportsView.as_view(), name='generate-last-n-days'),
# ]


# reports/manulreports/urls.py
from django.urls import path
from .reportslist.views import CountryReportListView, LatestCountryReportsView
from .reportview.views import ReportDetailView
from .overallreport.views import OverallReportView
from .manulreports.views import (
    YesterdayReportStatusView,
    GenerateYesterdayReportView,
)

urlpatterns = [
    path('reports/list/', CountryReportListView.as_view(), name='reports-list'),
    path('reports/latest/', LatestCountryReportsView.as_view(), name='latest-reports'),
    path('reports/view/', ReportDetailView.as_view(), name='report-detail'),
    path('overall-report/', OverallReportView.as_view(), name='overall-report'),

    # Simple report generation endpoints
    path('yesterday-status/', YesterdayReportStatusView.as_view(), name='yesterday-status'),
    path('generate-yesterday/', GenerateYesterdayReportView.as_view(), name='generate-yesterday'),
]