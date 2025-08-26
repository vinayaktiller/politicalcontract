from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch, Q
from ..models import Conversation, Message
from users.models import UserTree
from .serializers import ConversationListSerializer
from users.login.authentication import CookieJWTAuthentication



class ConversationListView(generics.ListAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationListSerializer

    def get_queryset(self):
        user = self.request.user
        conversations = Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).select_related('participant1', 'participant2')

        # Prefetch unread messages: status NOT 'read'/'read_update' and receiver=current user
        unread_msgs = Prefetch(
            'messages',
            queryset=Message.objects.filter(
                receiver=user
            ).exclude(
                status__in=['read', 'read_update']
            ),
            to_attr='unread_messages'
        )
        return conversations.prefetch_related(unread_msgs).order_by('-last_active')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = request.user

        # Get IDs of conversation partners to load UserTree
        other_user_ids = set()
        for conv in queryset:
            if conv.participant1_id == user.id:
                other_user_ids.add(conv.participant2_id)
            else:
                other_user_ids.add(conv.participant1_id)

        user_trees = UserTree.objects.filter(id__in=other_user_ids)
        user_tree_map = {ut.id: ut for ut in user_trees}

        context = self.get_serializer_context()
        context['user_tree_map'] = user_tree_map

        serializer = self.get_serializer(queryset, many=True, context=context)
        return Response(serializer.data)
