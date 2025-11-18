# api/serializers.py
from rest_framework import serializers
from ...models.groups import Group
from users.models.usertree import UserTree


class UserTreeSerializer(serializers.ModelSerializer):
    profilepic = serializers.SerializerMethodField()

    class Meta:
        model = UserTree
        fields = ['id', 'name', 'profilepic']

    def get_profilepic(self, obj):
        request = self.context.get('request')
        if obj.profilepic and hasattr(obj.profilepic, 'url'):
            return request.build_absolute_uri(obj.profilepic.url)
        return None

class GroupSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(source='id')
    group_name = serializers.CharField(source='name')
    founder = serializers.SerializerMethodField()
    speakers = serializers.SerializerMethodField()
    pending_speakers_details = serializers.SerializerMethodField()
    date_created = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Group
        fields = [
            'group_id', 'group_name', 'profile_pic', 'founder',
            'speakers', 'pending_speakers', 'pending_speakers_details',
            'date_created', 'institution', 'links', 'photos','members',
        ]

    def get_founder(self, obj):
        user_map = self.context.get('user_map', {})
        user = user_map.get(obj.founder)
        if user:
            return UserTreeSerializer(user, context=self.context).data
        return None

    def get_speakers(self, obj):
        user_map = self.context.get('user_map', {})
        serialized = []
        for user_id in obj.speakers:
            user = user_map.get(user_id)
            if user:
                serialized.append(UserTreeSerializer(user, context=self.context).data)
        return serialized

    def get_pending_speakers_details(self, obj):
        user_map = self.context.get('user_map', {})
        serialized = []
        for user_id in obj.pending_speakers:
            user = user_map.get(user_id)
            if user:
                serialized.append(UserTreeSerializer(user, context=self.context).data)
        return serialized