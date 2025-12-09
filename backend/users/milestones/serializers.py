from rest_framework import serializers
from ..models import Milestone

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        # API RULE: Exclude completed field from API responses
        fields = [
            'id', 'user_id', 'title', 'text', 'created_at', 
            'delivered', 'photo_id', 'photo_url', 'type'
        ]
