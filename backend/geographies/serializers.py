from rest_framework import serializers
from .models.geos import Country, State, District, Subdistrict, Village

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name', 'state']

class SubDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subdistrict
        fields = ['id', 'name', 'district']

class VillageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Village
        fields = ['id', 'name', 'subdistrict', 'status']