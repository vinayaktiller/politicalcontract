# urls.py
from django.urls import path
from .Journeyblog.views import JourneyBlogAPIView

urlpatterns = [
    path('journey-blogs/', JourneyBlogAPIView.as_view(), name='journey-blog-list'),
    path('journey-blogs/<uuid:pk>/', JourneyBlogAPIView.as_view(), name='journey-blog-detail'),
]