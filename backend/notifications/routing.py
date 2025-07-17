from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application
from .channels.notification_consumer import NotificationConsumer
from .channels.waitingpage_consumer import WaitingpageConsumer
# from .channels.Activity_consumer import ActivityConsumer
from django.urls import re_path

# yourapp/routing.py

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/waitingpage/(?P<user_email>[\w.@+-]+)/$', WaitingpageConsumer.as_asgi()),
    # re_path(r'ws/activity/today/', ActivityConsumer.as_asgi()),
    
]
