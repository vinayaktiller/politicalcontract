from rest_framework import serializers
from ..models import Contribution

class ContributionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = ['id', 'link', 'title', 'discription', 'owner']
        read_only_fields = ['id']   # ✅ auto-generated, not sent from frontend
