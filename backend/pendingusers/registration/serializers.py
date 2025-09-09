from rest_framework import serializers
from pendingusers.models import PendingUser

class PendingUserSerializer(serializers.ModelSerializer):
    has_no_initiator = serializers.BooleanField(write_only=True, required=False)
    
    class Meta:
        model = PendingUser
        fields = '__all__'
        extra_kwargs = {
            'initiator_id': {'required': False, 'allow_null': True}
        }
    
    def create(self, validated_data):
        # Extract has_no_initiator flag
        has_no_initiator = validated_data.pop('has_no_initiator', False)
        
        # If user has no initiator, ensure initiator_id is None
        if has_no_initiator:
            validated_data['initiator_id'] = None
        
        # Create the user
        user = PendingUser.objects.create(**validated_data)
        
        return user