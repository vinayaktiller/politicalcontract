from django.urls import path
from .channels.Activity_consumer import ActivityConsumer

websocket_urlpatterns = [
    path('ws/activity/today/', ActivityConsumer.as_asgi()),
]