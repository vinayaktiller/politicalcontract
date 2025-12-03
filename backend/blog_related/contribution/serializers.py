from rest_framework import serializers
from ..models import Contribution, ContributionConflict
from users.models import UserTree

class ContributionCreateSerializer(serializers.ModelSerializer):
    teammembers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Contribution
        fields = ['id', 'link', 'title', 'discription', 'type', 'owner', 'teammembers']
        read_only_fields = ['id']

class ContributionConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionConflict
        fields = [
            'id', 'contribution', 'conflict_type', 'explanation', 'evidence_urls',
            'disputed_title', 'disputed_description', 'disputed_type', 'disputed_teammembers', 
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']

class ContributionDetailSerializer(serializers.ModelSerializer):
    owner_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Contribution
        fields = ['id', 'link', 'title', 'type', 'owner', 'created_at', 'owner_details']
    
    def get_owner_details(self, obj):
        from users.models import UserTree
        from django.core.exceptions import ObjectDoesNotExist
        
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
        except ObjectDoesNotExist:
            return {
                'id': obj.owner,
                'name': f'User #{obj.owner}',
                'profile_pic': None
            }

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