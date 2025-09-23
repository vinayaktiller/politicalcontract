from rest_framework import serializers
from users.models import Petitioner, UserTree
from users.profilepic_manager.utils import get_profilepic_url

def get_profilepic_url(obj, request):
    if obj and hasattr(obj, 'profilepic') and obj.profilepic and hasattr(obj.profilepic, 'url') and request:
        return request.build_absolute_uri(obj.profilepic.url)
    return None

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
        return get_profilepic_url(obj['user_tree'], request)

    def get_has_conversation(self, obj):
        return obj['conversation_id'] is not None
