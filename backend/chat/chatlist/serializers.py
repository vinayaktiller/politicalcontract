from rest_framework import serializers
from chat.models import Conversation
from users.models import UserTree


class UserProfileSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()  # Handle name safely

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profilepic and request:
            return request.build_absolute_uri(obj.profilepic.url)
        return None

    def get_name(self, obj):
        # Safely handle name attribute
        return getattr(obj, 'name', f"User {obj.id}")

    class Meta:
        model = UserTree
        fields = ['id', 'name', 'profile_pic']


class ConversationListSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message_timestamp = serializers.DateTimeField(source='last_active', format="%Y-%m-%dT%H:%M:%S")

    def get_other_user(self, obj):
        user = self.context['request'].user
        other_user_id = obj.participant2_id if obj.participant1_id == user.id else obj.participant1_id
        user_tree_map = self.context.get('user_tree_map', {})
        other_user_tree = user_tree_map.get(other_user_id)

        if other_user_tree:
            return UserProfileSerializer(other_user_tree, context=self.context).data
        else:
            # Fallback for missing UserTree
            other_user = obj.participant2 if obj.participant1 == user else obj.participant1
            return {
                'id': other_user_id,
                'name': f"{other_user.first_name} {other_user.last_name}",
                'profile_pic': None
            }

    def get_unread_count(self, obj):
        current_user = self.context['request'].user
        unread_messages = getattr(obj, 'unread_messages', [])
        # Count messages where sender is not current user and status is NOT 'read' or 'read_update'
        return sum(
            1 for msg in unread_messages
            if msg.sender != current_user and msg.status not in ['read', 'read_update']
        )

    class Meta:
        model = Conversation
        fields = [
            'id',
            'other_user',
            'last_message',
            'last_message_timestamp',
            'unread_count'
        ]
