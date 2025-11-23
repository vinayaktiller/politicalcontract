from rest_framework import serializers
from ..services.blog_creation import BlogCreationService



class BlogCreateSerializer(serializers.Serializer):
    # Common fields
    type = serializers.ChoiceField(choices=BlogCreationService.BLOG_TYPES)
    content_type = serializers.ChoiceField(choices=BlogCreationService.CONTENT_TYPES)
    userid = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.CharField(required=False)

    # Type-specific fields
    target_user = serializers.IntegerField(required=False, allow_null=True)
    milestone_id = serializers.CharField(required=False, allow_null=True)
    report_type = serializers.CharField(required=False, allow_null=True)
    report_id = serializers.CharField(required=False, allow_null=True)
    url = serializers.URLField(required=False, allow_null=True)
    contribution = serializers.CharField(required=False, allow_null=True)
    questionid = serializers.IntegerField(required=False, allow_null=True)
    country_id = serializers.IntegerField(required=False, allow_null=True)
    state_id = serializers.IntegerField(required=False, allow_null=True)
    district_id = serializers.IntegerField(required=False, allow_null=True)
    subdistrict_id = serializers.IntegerField(required=False, allow_null=True)
    village_id = serializers.IntegerField(required=False, allow_null=True)
    target_details = serializers.CharField(required=False, allow_null=True)
    failure_reason = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        """Use BlogCreationService to handle blog creation"""
        creation_service = BlogCreationService(validated_data)
        return creation_service.create_blog()