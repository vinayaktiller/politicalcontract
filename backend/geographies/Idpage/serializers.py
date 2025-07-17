from rest_framework import serializers

class GeoEntitySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()

class IDBreakdownSerializer(serializers.Serializer):
    id = serializers.CharField()
    state = GeoEntitySerializer()
    district = GeoEntitySerializer()
    subdistrict = GeoEntitySerializer()
    village = GeoEntitySerializer()
    person_code = serializers.CharField()