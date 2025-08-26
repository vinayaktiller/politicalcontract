from django.urls import path
from .contribution.views import ContributionCreateView   # or .news if in news.py
from .uservalidation.views import validate_users
from .contribution_related.id_retrival import views
from .Question.views import QuestionListAPI

urlpatterns = [
    path('contributions/create/', ContributionCreateView.as_view(), name='contribution-create'),
    path('validate-users/', validate_users, name='validate-users'),
    path('get-contribution/', views.get_or_create_contribution_by_link, name='get-or-create-contribution-by-link'),
    path('questions/', QuestionListAPI.as_view(), name='question-list'),
    path('contributions/<uuid:contribution_id>/', views.delete_contribution, name='delete-contribution'),
    
]
