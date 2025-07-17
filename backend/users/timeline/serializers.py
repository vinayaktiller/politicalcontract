from rest_framework import serializers
from ..models.usertree import UserTree
from ..models import Circle

class ProfileSerializer(serializers.ModelSerializer):
    profilepic = serializers.SerializerMethodField()
    
    class Meta:
        model = UserTree
        fields = [
            'id', 'name', 'profilepic', 
            'childcount', 'influence', 
            'height', 'weight', 'depth'
        ]
    
    def get_profilepic(self, obj):
        request = self.context.get('request')
        if obj.profilepic and hasattr(obj.profilepic, 'url') and request is not None:
            return request.build_absolute_uri(obj.profilepic.url)
        return None


class ExtendedProfileSerializer(ProfileSerializer):
    initiates = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    connections = serializers.SerializerMethodField()
    groupmembers = serializers.SerializerMethodField()  # New field
    
    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + [
            'initiates', 'members', 'connections', 'groupmembers'
        ]
    
    def _get_relation_profiles(self, obj, relation_type):
        context = self.context
        circles_by_user = context.get('circles_by_user', {})
        profile_map = context.get('profile_map', {})
        
        # Use prefetched data if available
        if obj.id in circles_by_user and relation_type in circles_by_user[obj.id]:
            circles = circles_by_user[obj.id][relation_type]
            otherperson_ids = [c.otherperson for c in circles if c.otherperson]
            profiles = [profile_map[pid] for pid in otherperson_ids if pid in profile_map]
        else:  # Fallback to DB query
            circles = Circle.objects.filter(
                userid=obj.id,
                onlinerelation=relation_type
            )
            otherperson_ids = [circle.otherperson for circle in circles if circle.otherperson]
            profiles = UserTree.objects.filter(id__in=otherperson_ids)
        
        serializer = ProfileSerializer(profiles, many=True, context=self.context)
        return serializer.data
    
    def get_initiates(self, obj):
        return self._get_relation_profiles(obj, 'initiate')
    
    def get_members(self, obj):
        return self._get_relation_profiles(obj, 'members')
    
    def get_connections(self, obj):
        return self._get_relation_profiles(obj, 'connections')
    
    def get_groupmembers(self, obj):
        return self._get_relation_profiles(obj, 'groupmembers')