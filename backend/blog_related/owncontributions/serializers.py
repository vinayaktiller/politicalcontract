from rest_framework import serializers
from ..models import Contribution
from users.models import UserTree

class ContributionListSerializer(serializers.ModelSerializer):
    owner_details = serializers.SerializerMethodField()
    team_member_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Contribution
        fields = [
            'id', 'link', 'title', 'discription', 'type', 'owner', 
            'teammembers', 'created_at', 'updated_at',
            'owner_details', 'team_member_details'
        ]
    
    def get_owner_details(self, obj):
        if not obj.owner:
            return None
        try:
            owner_user = UserTree.objects.get(id=obj.owner)
            request = self.context.get('request')
            return {
                'id': owner_user.id,
                'name': owner_user.name,
                'profile_pic': request.build_absolute_uri(owner_user.profilepic.url) if owner_user.profilepic and request else None
            }
        except UserTree.DoesNotExist:
            return {
                'id': obj.owner,
                'name': f'User #{obj.owner}',
                'profile_pic': None
            }
    
    def get_team_member_details(self, obj):
        if not obj.teammembers:
            return []
        
        team_members = []
        for member_id in obj.teammembers:
            try:
                member = UserTree.objects.get(id=member_id)
                request = self.context.get('request')
                team_members.append({
                    'id': member.id,
                    'name': member.name,
                    'profile_pic': request.build_absolute_uri(member.profilepic.url) if member.profilepic and request else None
                })
            except UserTree.DoesNotExist:
                team_members.append({
                    'id': member_id,
                    'name': f'User #{member_id}',
                    'profile_pic': None
                })
        return team_members