from django.urls import path
from .chatlist.views import ConversationListView
from .chatroom.views import (
    ConversationDetailView,
    MessageListView,
    SendMessageView,
    MarkAsReadView
)
from .contact_list.views import contact_list, start_conversation
# from contact_list.views import ContactListAPIView, StartConversationAPIView

urlpatterns = [
    # Chat list endpoints
    path('chatlist/', ConversationListView.as_view(), name='chat-list'),
    
    # Conversation endpoints
    path('conversations/<uuid:conversation_id>/', 
         ConversationDetailView.as_view(), 
         name='conversation-detail'),
    
    # Message endpoints
    path('chat/<uuid:conversation_id>/messages/', 
         MessageListView.as_view(), 
         name='chat-messages'),
    path('chat/<uuid:conversation_id>/send/', 
         SendMessageView.as_view(), 
         name='chat-send'),
    path('chat/<uuid:conversation_id>/mark_read/', 
         MarkAsReadView.as_view(), 
         name='chat-mark-read'),
    path('contacts/', contact_list, name='contact_list'),
    path('conversation/start/<int:contact_id>/', start_conversation, name='start_conversation'),
     # path('contacts/', ContactListAPIView.as_view(), name='contact-list'),
     # path('start-conversation/<int:contact_id>/', StartConversationAPIView.as_view(), name='start-conversation'),

 ]