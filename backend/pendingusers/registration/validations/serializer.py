from users.models.usertree import UserTree
from rest_framework import serializers

class InitiatorIdSerializer(serializers.ModelSerializer):
    profilepic = serializers.SerializerMethodField()

    class Meta:
        model = UserTree
        fields = ['id', 'name', 'profilepic']

    def get_profilepic(self, obj):
        request = self.context.get('request')
        if obj.profilepic and hasattr(obj.profilepic, 'url'):
            
            return request.build_absolute_uri(obj.profilepic.url)
        return None
