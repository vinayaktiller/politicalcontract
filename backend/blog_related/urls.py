from django.urls import path
from .contribution.views import ContributionCreateView   # or .news if in news.py

urlpatterns = [
    path('contributions/create/', ContributionCreateView.as_view(), name='contribution-create'),
]
