from django.urls import re_path
from .channels.message_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>[^/]+)/$', ChatConsumer.as_asgi()),
]