from rest_framework import serializers

class LandingResponseSerializer(serializers.Serializer):
    user_type = serializers.CharField()
    user_email = serializers.EmailField()
    user_id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_pic = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    message = serializers.CharField(required=False)