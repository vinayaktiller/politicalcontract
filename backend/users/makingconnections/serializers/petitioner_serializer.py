from rest_framework import serializers
from users.models.petitioners import Petitioner
from users.models.usertree import UserTree  # Assuming correct import path

class PetitionerSerializer(serializers.ModelSerializer):
    country = serializers.StringRelatedField()
    state = serializers.StringRelatedField()
    district = serializers.StringRelatedField()
    subdistrict = serializers.StringRelatedField()
    village = serializers.StringRelatedField()
    profile_picture = serializers.SerializerMethodField()  # Changed field name

    class Meta:
        model = Petitioner
        fields = [
            'gmail', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'country', 'state', 'district', 'subdistrict', 'village', 'profile_picture', 'id'  # Updated field
        ]

    def get_profile_picture(self, obj):
        """
        Fetches profile_picture from UserTree using the petitioner's ID.
        Assumes that UserTree has an entry with the same ID as the Petitioner.
        """
        base_url = "http://localhost:8000/"
        user_tree = UserTree.objects.filter(id=obj.id).first()

        if user_tree and user_tree.profilepic and hasattr(user_tree.profilepic, 'url'):
            return f"{base_url}{user_tree.profilepic.url.lstrip('/')}"

        return None
