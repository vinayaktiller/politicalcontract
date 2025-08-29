# serializers.py
from rest_framework import serializers
from ..models import Contribution, ContributionConflict

class ContributionCreateSerializer(serializers.ModelSerializer):
    teammembers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Contribution
        fields = ['id', 'link', 'title', 'discription', 'owner', 'teammembers']
        read_only_fields = ['id']

class ContributionConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionConflict
        fields = [
            'id', 'contribution', 'conflict_type', 'explanation', 'evidence_urls',
            'disputed_title', 'disputed_description', 'disputed_teammembers', 
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']

class ContributionDetailSerializer(serializers.ModelSerializer):
    owner_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Contribution
        fields = ['id', 'link', 'title', 'owner', 'created_at', 'owner_details']
    
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