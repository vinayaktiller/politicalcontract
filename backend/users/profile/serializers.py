# users/profile/serializers.py

from rest_framework import serializers
from users.models import Petitioner, Milestone, Circle, UserTree
from event.models import Group
from ..profilepic_manager.utils import get_profilepic_url

class CountrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class StateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    country = CountrySerializer()

class DistrictSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    state = StateSerializer()

class SubdistrictSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    district = DistrictSerializer()

class VillageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subdistrict = SubdistrictSerializer()

class UserSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    state = StateSerializer()
    district = DistrictSerializer()
    subdistrict = SubdistrictSerializer()
    village = VillageSerializer()

    class Meta:
        model = Petitioner
        fields = '__all__'

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    state = StateSerializer()
    district = DistrictSerializer()
    subdistrict = SubdistrictSerializer()
    village = VillageSerializer()

    class Meta:
        model = Group
        fields = '__all__'
class ProfileSerializer(serializers.ModelSerializer):
    profilepic = serializers.SerializerMethodField()
    
    class Meta:
        model = UserTree
        fields = [
            'id', 'name', 'profilepic', 
            'childcount', 'influence', 
            'height', 'weight', 'depth'
        ]
    
    def get_profilepic(self, obj):
        request = self.context.get('request')
        return get_profilepic_url(obj, request)