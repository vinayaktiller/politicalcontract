from rest_framework import serializers
from chat.models import Message, Conversation
from users.models import UserTree

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_profile = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    
    class Meta:
        model = Message
        fields = [
            'id', 'content', 'timestamp', 'read', 'delivered',
            'sender_name', 'sender_profile', 'is_own'
        ]
    
    def get_sender_name(self, obj):
        user_tree_map = self.context.get('user_tree_map', {})
        user_tree = user_tree_map.get(obj.sender_id)
        if user_tree:
            return user_tree.name
        # Fallback to Petitioner's name
        return f"{obj.sender.first_name} {obj.sender.last_name}"
        
    def get_sender_profile(self, obj):
        user_tree_map = self.context.get('user_tree_map', {})
        user_tree = user_tree_map.get(obj.sender_id)
        if user_tree:
            request = self.context.get('request')
            if user_tree.profilepic and request:
                return request.build_absolute_uri(user_tree.profilepic.url)
        return None
        
    def get_is_own(self, obj):
        return obj.sender == self.context['request'].user

class ConversationDetailSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    
    def get_other_user(self, obj):
        user = self.context['request'].user
        other_user_id = obj.participant2_id if obj.participant1_id == user.id else obj.participant1_id
        
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
        profile_pic = None
        if user_tree.profilepic and request:
            profile_pic = request.build_absolute_uri(user_tree.profilepic.url)
        return {
            'id': user_tree.id,
            'name': user_tree.name,
            'profile_pic': profile_pic
        }
    
    class Meta:
        model = Conversation
        fields = ['id', 'other_user']