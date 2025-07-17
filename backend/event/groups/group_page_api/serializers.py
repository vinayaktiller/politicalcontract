from rest_framework import serializers
from ...models.groups import Group
from users.models.usertree import UserTree

class UserTreeSerializer(serializers.ModelSerializer):
    profilepic = serializers.SerializerMethodField()

    class Meta:
        model = UserTree
        fields = ['id', 'name', 'profilepic']

    def get_profilepic(self, obj):
        if obj.profilepic:
            return self.context['request'].build_absolute_uri(obj.profilepic.url)
        return None

class GroupSerializer(serializers.ModelSerializer):
    founder = serializers.SerializerMethodField()
    speakers = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'profile_pic', 'founder',
            'speakers', 'members_count', 'created_at',
            'institution', 'links', 'photos'
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

    def get_members_count(self, obj):
        return len(obj.members)
