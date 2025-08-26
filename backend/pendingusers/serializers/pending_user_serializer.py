from rest_framework import serializers
from pendingusers.models import PendingUser
from rest_framework import serializers
from geographies.models.geos import Country, State, District, Subdistrict, Village

class CountryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name']

class StateNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['name']

class DistrictNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['name']

class SubdistrictNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subdistrict
        fields = ['name']

class VillageNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Village
        fields = ['name']


class PendingUserSerializer(serializers.ModelSerializer):
    country = serializers.CharField(source='country.name', read_only=True)
    state = serializers.CharField(source='state.name', read_only=True)
    district = serializers.CharField(source='district.name', read_only=True)
    subdistrict = serializers.CharField(source='subdistrict.name', read_only=True)
    village = serializers.CharField(source='village.name', read_only=True)
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = PendingUser
        fields = [
            'gmail', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'country', 'state', 'district', 'subdistrict', 'village',
            'is_verified', 'event_type', 'event_id', 'initiator_id',
            'profile_picture'
        ]

    def get_profile_picture(self, obj):
        base_url = "http://localhost:8000/"
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return f"{base_url}{obj.profile_picture.url.lstrip('/')}"
        return None
