# serializers/phone_number_serializer.py
from rest_framework import serializers
from pendingusers.models.no_initiator_user import NoInitiatorUser

class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoInitiatorUser
        fields = ['phone_number']
        
    def validate_phone_number(self, value):
        # Basic phone number validation
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Please enter a valid phone number.")
        return value