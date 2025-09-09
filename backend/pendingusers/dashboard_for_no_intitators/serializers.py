# serializers.py
from rest_framework import serializers
from ..models import PendingUser, NoInitiatorUser

class NoInitiatorUserSerializer(serializers.ModelSerializer):
    claimed_by_name = serializers.CharField(source='claimed_by.user.username', read_only=True)
    
    class Meta:
        model = NoInitiatorUser
        fields = '__all__'

class PendingUserNoInitiatorSerializer(serializers.ModelSerializer):
    no_initiator_data = NoInitiatorUserSerializer(read_only=True)
    country_name = serializers.CharField(source='country.name', read_only=True)
    state_name = serializers.CharField(source='state.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    subdistrict_name = serializers.CharField(source='subdistrict.name', read_only=True)
    village_name = serializers.CharField(source='village.name', read_only=True)

    class Meta:
        model = PendingUser
        fields = [
            'id', 'gmail', 'first_name', 'last_name', 'profile_picture', 
            'date_of_birth', 'gender', 'country_name', 'state_name', 
            'district_name', 'subdistrict_name', 'village_name', 
            'is_verified', 'event_type', 'event_id', 'no_initiator_data'
        ]