from rest_framework import serializers
from ...models import Group
from geographies.models.geos import Country, State, District, Subdistrict, Village

class GroupRegistrationSerializer(serializers.ModelSerializer):
    founder = serializers.IntegerField(write_only=True)
    speakers = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        default=[]
    )
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        write_only=True
    )
    state = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(),
        write_only=True
    )
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        write_only=True
    )
    subdistrict = serializers.PrimaryKeyRelatedField(
        queryset=Subdistrict.objects.all(),
        write_only=True
    )
    village = serializers.PrimaryKeyRelatedField(
        queryset=Village.objects.all(),
        write_only=True
    )
    institution = serializers.CharField(
        max_length=255,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = Group
        fields = [
            'name',
            'founder',
            'speakers',
            'country',
            'state',
            'district',
            'subdistrict',
            'village',
            'institution',
        ]
    
    def create(self, validated_data):
        # Extract speakers from validated data
        speakers = validated_data.pop('speakers', [])
        
        # Create the group instance
        group = Group.objects.create(**validated_data)
        
        # Set speakers if provided
        if speakers:
            group.speakers = speakers
            group.save()
            
        return group