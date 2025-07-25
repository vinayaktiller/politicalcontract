from rest_framework import serializers
from users.models import Petitioner, UserTree


class ContactSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()
    has_conversation = serializers.SerializerMethodField()  # Changed here!
    conversation_id = serializers.UUIDField(allow_null=True)

    def get_name(self, obj):
        return f"{obj['petitioner'].first_name} {obj['petitioner'].last_name}"

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj['user_tree'].profilepic:
            return request.build_absolute_uri(obj['user_tree'].profilepic.url)
        return None

    def get_has_conversation(self, obj):
        return obj['conversation_id'] is not None
