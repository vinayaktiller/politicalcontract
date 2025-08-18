# urls.py
from django.urls import path
from .Journeyblog.views import JourneyBlogAPIView
from .posting_blogs.views import BlogCreateAPIView
from .circleconcontacts.views import CircleContactsView

urlpatterns = [
    path('journey-blogs/', JourneyBlogAPIView.as_view(), name='journey-blog-list'),
    path('journey-blogs/<uuid:pk>/', JourneyBlogAPIView.as_view(), name='journey-blog-detail'),
    path('create-blog/', BlogCreateAPIView.as_view(), name='create-blog'),
    path('circle-contacts/', CircleContactsView.as_view(), name='circle-contacts'),

]