from rest_framework import serializers
from ...models.groups import Group
from users.models.usertree import UserTree

class UserTreeSerializer(serializers.ModelSerializer):
    profilepic = serializers.SerializerMethodField()

    class Meta:
        model = UserTree
        fields = ['id', 'name', 'profilepic','audience_count','shared_audience_count']

    def get_profilepic(self, obj):
        request = self.context.get('request')
        if obj.profilepic and hasattr(obj.profilepic, 'url'):
            return request.build_absolute_uri(obj.profilepic.url)
        return None

class GroupDetailSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(source='id')
    group_name = serializers.CharField(source='name')
    date_created = serializers.DateTimeField(source='created_at')
    founder = serializers.SerializerMethodField()
    speakers = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    outside_agents = serializers.SerializerMethodField()
    # use StringRelatedField to get .__str__() of each location FK
    country = serializers.StringRelatedField()
    state = serializers.StringRelatedField()
    district = serializers.StringRelatedField()
    subdistrict = serializers.StringRelatedField()
    village = serializers.StringRelatedField()

    class Meta:
        model = Group
        fields = [
            'group_id',
            'group_name',
            'profile_pic',
            'founder',
            'speakers',
            'members',
            'outside_agents',
            'country',
            'state',
            'district',
            'subdistrict',
            'village',
            'institution',
            'links',
            'photos',
            'date_created',
        ]

    def _get_users(self, ids):
        """Helper: look up UserTree instances in the user_map context."""
        user_map = self.context.get('user_map', {})
        return [
            UserTreeSerializer(user_map[uid], context=self.context).data
            for uid in ids
            if uid in user_map
        ]

    def get_founder(self, obj):
        user_map = self.context.get('user_map', {})
        user = user_map.get(obj.founder)
        if user:
            return UserTreeSerializer(user, context=self.context).data
        return None

    def get_speakers(self, obj):
        return self._get_users(obj.speakers)

    def get_members(self, obj):
        return self._get_users(obj.members)

    def get_outside_agents(self, obj):
        return self._get_users(obj.outside_agents)
