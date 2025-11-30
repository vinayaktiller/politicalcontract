from django.urls import path
from .activityreportview.views import ActivityReportDetailView
from .activityreportslist.views import CountryActivityReportListView, LatestCountryActivityReportsView
from .heartbeat.views import CheckActivityView, MarkActiveView, ActivityHistoryView
from .heartbeat.HeartbeatNetworkView import HeartbeatNetworkView

urlpatterns = [
    path('activity-report/', ActivityReportDetailView.as_view(), name='activity-report-detail'),
    path('activity-reports/list/', CountryActivityReportListView.as_view(), name='country-activity-reports-list'),
    path('activity-reports/latest/', LatestCountryActivityReportsView.as_view(), name='latest-country-activity-reports'),
    path('heartbeat/check-activity/', CheckActivityView.as_view(), name='check-activity'),
    path('heartbeat/mark-active/', MarkActiveView.as_view(), name='mark-active'),
    path('heartbeat/activity-history/', ActivityHistoryView.as_view(), name='activity-history'),
    path('heartbeat/network/', HeartbeatNetworkView.as_view(), name='heartbeat-network'),

]