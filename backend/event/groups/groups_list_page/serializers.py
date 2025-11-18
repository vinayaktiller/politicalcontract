from rest_framework import serializers
from ...models.groups import Group

class UserGroupSerializer(serializers.Serializer):
    group_id = serializers.IntegerField(source='id')
    group_name = serializers.CharField(source='name')
    group_type = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    # Use method field for profile_pic
    profile_pic = serializers.SerializerMethodField()

    def get_group_type(self, obj):
        """Determine group type based on members"""
        return "unstarted" if not obj.members else "old"

    def get_date_created(self, obj):
        """Return only date part without time"""
        return obj.created_at.date()
    
    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if obj.profile_pic and hasattr(obj.profile_pic, 'url'):
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None

