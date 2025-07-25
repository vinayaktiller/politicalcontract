from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from ..models import Conversation, Message
from users.models import UserTree
from .serializers import MessageSerializer, ConversationDetailSerializer

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

class ConversationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationDetailSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'conversation_id'  # Match frontend parameter name

    def get_queryset(self):
        return Conversation.objects.filter(
            Q(participant1=self.request.user) | 
            Q(participant2=self.request.user)
        )
    
    def get_object(self):
        obj = super().get_object()
        obj.last_active = timezone.now()
        obj.save(update_fields=['last_active'])
        
        # Prefetch UserTree for participants
        participant_ids = [obj.participant1_id, obj.participant2_id]
        user_trees = UserTree.objects.filter(id__in=participant_ids)
        obj.user_tree_map = {ut.id: ut for ut in user_trees}
        
        return obj

class MessageListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return Message.objects.filter(
            Q(conversation__id=conversation_id) &
            (Q(conversation__participant1=self.request.user) | 
             Q(conversation__participant2=self.request.user))
        ).order_by('timestamp')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Get sender IDs
        sender_ids = set(queryset.values_list('sender_id', flat=True))
        
        # Fetch related UserTree objects
        user_trees = UserTree.objects.filter(id__in=sender_ids)
        user_tree_map = {ut.id: ut for ut in user_trees}
        
        # Pass to serializer context
        context = self.get_serializer_context()
        context['user_tree_map'] = user_tree_map
        
        serializer = self.get_serializer(queryset, many=True, context=context)
        return Response(serializer.data)


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                Q(id=conversation_id) & 
                (Q(participant1=request.user) | 
                 Q(participant2=request.user))
            )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found or access denied"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        content = request.data.get('content')
        if not content:
            return Response(
                {"error": "Message content required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine receiver automatically
        if request.user == conversation.participant1:
            receiver = conversation.participant2
        else:
            receiver = conversation.participant1
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        # Update conversation last message
        conversation.last_message = content
        conversation.last_message_timestamp = message.timestamp
        conversation.last_active = message.timestamp
        conversation.save()
        
        # Get UserTree for sender
        try:
            sender_tree = UserTree.objects.get(id=request.user.id)
            user_tree_map = {request.user.id: sender_tree}
        except UserTree.DoesNotExist:
            user_tree_map = {}
        
        serializer = MessageSerializer(message, context={
            'request': request,
            'user_tree_map': user_tree_map
        })
        
        # If receiver is offline, log it but don't deliver immediately
        if not receiver.is_online:
            logger.info(f"Receiver {receiver.id} is offline. Message will be delivered when online.")
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(
                Q(id=conversation_id) & 
                (Q(participant1=request.user) | 
                 Q(participant2=request.user))
            )
            # Mark messages as read
            messages = Message.objects.filter(
                conversation=conversation,
                read=False,
                receiver=request.user  # Only mark messages received by this user
            )
            
            for message in messages:
                message.mark_as_read()
            
            return Response({"status": "marked as read"})
            
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )