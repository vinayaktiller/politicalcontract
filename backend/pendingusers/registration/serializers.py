from rest_framework import serializers
from pendingusers.models import PendingUser

class PendingUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUser
        fields = '__all__'
