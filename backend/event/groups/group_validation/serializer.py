from rest_framework import serializers
from ...models import Group
from users.models.usertree import UserTree

class GroupSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()
    profile_source = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id',
            'name',
            'profile_pic',
            'profile_source',
        ]
       

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        
        # 1. Check if group has its own profile picture
        if obj.profile_pic:
            return request.build_absolute_uri(obj.profile_pic) if request else obj.profile_pic
        
        # 2. Fallback to founder's profile picture
        try:
            founder = UserTree.objects.get(id=obj.founder)
            if founder.profilepic:
                return request.build_absolute_uri(founder.profilepic.url) if request else founder.profilepic.url
        except UserTree.DoesNotExist:
            pass
        
        # 3. Return default if no images found
        return None

    def get_profile_source(self, obj):
        if obj.profile_pic:
            return "group"
        elif obj.founder:
            return "founder"
        return None