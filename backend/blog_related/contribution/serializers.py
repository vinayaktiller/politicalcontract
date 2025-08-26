# serializers.py
from rest_framework import serializers
from ..models import Contribution

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