# serializers.py
from rest_framework import serializers
from ...models.groups import Group

class UserGroupSerializer(serializers.Serializer):
    group_id = serializers.IntegerField(source='id')
    group_name = serializers.CharField(source='name')
    group_type = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    profile_pic = serializers.URLField(allow_null=True)

    def get_group_type(self, obj):
        """Determine group type based on members"""
        return "unstarted" if not obj.members else "old"

    def get_date_created(self, obj):
        """Return only date part without time"""
        return obj.created_at.date()