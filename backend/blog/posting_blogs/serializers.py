from rest_framework import serializers
from ..models import *
from uuid import UUID
import re

class BlogCreateSerializer(serializers.Serializer):
    BLOG_TYPES = [
        'journey', 'successful_experience', 'milestone',
        'report_insight', 'failed_initiation', 'consumption', 'answering_question'
    ]

    CONTENT_TYPES = ['micro', 'short_essay', 'article']

    # Common fields
    type = serializers.ChoiceField(choices=BLOG_TYPES)
    content_type = serializers.ChoiceField(choices=CONTENT_TYPES)
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

    def validate(self, data):
        # Content validation
        if data['type'] != 'failed_initiation' and not data.get('content'):
            raise serializers.ValidationError("Content is required for this blog type")

        # Type-specific field validation
        if data['type'] == 'journey' and not data.get('target_user'):
            raise serializers.ValidationError("target_user is required for journey blogs")

        if data['type'] == 'successful_experience' and not data.get('target_user'):
            raise serializers.ValidationError("target_user is required for successful experience blogs")

        if data['type'] == 'milestone' and not data.get('milestone_id'):
            raise serializers.ValidationError("milestone_id is required for milestone blogs")

        if data['type'] == 'report_insight' and (not data.get('report_type') or not data.get('report_id')):
            raise serializers.ValidationError("report_type and report_id are required for report insights")

        if data['type'] == 'consumption' and (not data.get('url') or not data.get('contribution')):
            raise serializers.ValidationError("url and contribution are required for consumption blogs")

        if data['type'] == 'answering_question' and not data.get('questionid'):
            raise serializers.ValidationError("questionid is required for answering questions")

        if data['type'] == 'failed_initiation' and (not data.get('failure_reason') or not data.get('target_details')):
            raise serializers.ValidationError("failure_reason and target_details are required for failed initiations")

        # UUID validation
        for field in ['milestone_id', 'contribution']:
            if data.get(field):
                try:
                    UUID(data[field])
                except ValueError:
                    raise serializers.ValidationError(f"{field} must be a valid UUID")

        return data

    def create(self, validated_data):
        blog_type = validated_data.pop('type')
        content_type = validated_data.pop('content_type')
        content = validated_data.pop('content', None)

        # Create base blog
        base_blog = BaseBlogModel.objects.create(
            userid=validated_data.get('userid'),
            type=f"{blog_type}_{content_type}"
        )

        # Handle different blog types
        if blog_type == 'journey':
            model_map = {
                'micro': MicroJourneyBlog,
                'short_essay': ShortEssayJourneyBlog,
                'article': ArticleJourneyBlog
            }
            blog = model_map[content_type].objects.create(
                id=base_blog.id,
                target_user=validated_data['target_user'],
                content=content
            )

        elif blog_type == 'successful_experience':
            model_map = {
                'micro': MicroSuccessfulExperience,
                'short_essay': ShortEssaySuccessfulExperience,
                'article': ArticleSuccessfulExperience
            }
            blog = model_map[content_type].objects.create(
                id=base_blog.id,
                target_user=validated_data['target_user'],
                content=content
            )

        elif blog_type == 'milestone':
            model_map = {
                'micro': MicroMilestoneJourneyBlog,
                'short_essay': ShortEssayMilestoneJourneyBlog,
                'article': ArticleMilestoneJourneyBlog
            }
            blog = model_map[content_type].objects.create(
                id=base_blog.id,
                target_user=validated_data['target_user'],
                milestone_id=validated_data['milestone_id'],
                content=content
            )

        elif blog_type == 'report_insight':
            model_map = {
                'micro': micro_report_insight_blog,
                'short_essay': short_essay_report_insight_blog,
                'article': article_report_insight_blog
            }
            blog = model_map[content_type].objects.create(
                id=base_blog.id,
                report_type=validated_data['report_type'],
                report_id=validated_data['report_id'],
                content=content
            )

        elif blog_type == 'consumption':
            model_map = {
                'micro': MicroConsumption,
                'short_essay': ShortEssayConsumption,
                'article': ArticleConsumption
            }
            blog = model_map[content_type].objects.create(
                id=base_blog.id,
                url=validated_data['url'],
                contribution=validated_data['contribution'],
                content=content
            )

        elif blog_type == 'answering_question':
            model_map = {
                'micro': MicroAnsweringQuestionBlog,
                'short_essay': ShortEssayAnsweringQuestionBlog,
                'article': ArticleAnsweringQuestionBlog
            }
            blog = model_map[content_type].objects.create(
                id=base_blog.id,
                questionid=validated_data['questionid'],
                content=content
            )

        elif blog_type == 'failed_initiation':
            model_map = {
                'micro': MicroFailedInitiationExperience,
                'short_essay': ShortEssayFailedInitiationExperience,
                'article': ArticleFailedInitiationExperience
            }
            concrete_model = model_map[content_type]
            
            blog = concrete_model.objects.create(
                id=base_blog.id,
                country_id=validated_data.get('country_id'),
                state_id=validated_data.get('state_id'),
                district_id=validated_data.get('district_id'),
                subdistrict_id=validated_data.get('subdistrict_id'),
                village_id=validated_data.get('village_id'),
                target_details=validated_data['target_details'],
                failure_reason=validated_data['failure_reason'],
                content=content  # Add content field
            )

        else:
            raise serializers.ValidationError(f"Unsupported blog type: {blog_type}")

        return blog
