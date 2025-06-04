from rest_framework import serializers
from pendingusers.models import PendingUser

class PendingUserSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField()
    state = serializers.StringRelatedField()
    district = serializers.StringRelatedField()
    subdistrict = serializers.StringRelatedField()
    village = serializers.StringRelatedField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = PendingUser
        fields = [
            'gmail', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'country', 'state', 'district', 'subdistrict', 'village',
            'is_verified', 'event_type', 'event_id', 'initiator_id',
            'profile_picture'
        ]

    # def get_profile_picture(self, obj):
    #     request = self.context.get('request')

    #     if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
    #         if request is not None:
    #             print(request.build_absolute_uri(obj.profile_picture.url))
    #             return request.build_absolute_uri(obj.profile_picture.url)
    #         else:
    #             print(obj.profile_picture.url)
    #             return obj.profile_picture.url
    #     return None
    def get_profile_picture(self, obj):
        base_url = "http://localhost:8000/"

        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return f"{base_url}{obj.profile_picture.url.lstrip('/')}"
        
        return None
