from rest_framework import serializers
from chat.models import Message, Conversation
from users.models import UserTree  # Ensure UserTree is imported as used
from users.profilepic_manager.utils import get_profilepic_url

def get_profilepic_url(obj, request):
    if obj and hasattr(obj, 'profilepic') and obj.profilepic and hasattr(obj.profilepic, 'url') and request:
        return request.build_absolute_uri(obj.profilepic.url)
    return None

class MessageSerializer(serializers.ModelSerializer):
    status = serializers.CharField()  # Always capture the backend value (not get_status_display)
    sender_name = serializers.SerializerMethodField()
    sender_profile = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")

    class Meta:
        model = Message
        fields = [
            'id', 'content', 'timestamp', 'status',
            'sender_name', 'sender_profile', 'is_own'
        ]

    def to_representation(self, instance):
        """Ensure status is always lowercase (standard backend value)."""
        data = super().to_representation(instance)
        if 'status' in data and data['status']:
            data['status'] = str(data['status']).lower()  # Defensive lowercase
        return data

    def get_sender_name(self, obj):
        user_tree_map = self.context.get('user_tree_map', {})
        user_tree = user_tree_map.get(obj.sender_id)
        if user_tree:
            return user_tree.name
        # Fallback to Petitioner's first and last name
        return f"{obj.sender.first_name} {obj.sender.last_name}"

    def get_sender_profile(self, obj):
        user_tree_map = self.context.get('user_tree_map', {})
        user_tree = user_tree_map.get(obj.sender_id)
        request = self.context.get('request')
        if user_tree:
            return get_profilepic_url(user_tree, request)
        return None

    def get_is_own(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return False
        return obj.sender == request.user


class ConversationDetailSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_user']

    def get_other_user(self, obj):
        request = self.context.get('request')
        user = request.user if request else None

        # Detect which is the 'other' user
        other_user_id = obj.participant2_id if obj.participant1_id == getattr(user, 'id', None) else obj.participant1_id

        # Use prefetched UserTree if available
        if hasattr(obj, 'user_tree_map'):
            user_tree = obj.user_tree_map.get(other_user_id)
            if user_tree:
                return self.get_user_profile_data(user_tree)

        # Fallback to Petitioner data
        other_user = obj.participant2 if obj.participant1 == user else obj.participant1
        return {
            'id': other_user_id,
            'name': f"{other_user.first_name} {other_user.last_name}",
            'profile_pic': None
        }

    def get_user_profile_data(self, user_tree):
        request = self.context.get('request')
        profile_pic = get_profilepic_url(user_tree, request)
        return {
            'id': user_tree.id,
            'name': user_tree.name,
            'profile_pic': profile_pic
        }
