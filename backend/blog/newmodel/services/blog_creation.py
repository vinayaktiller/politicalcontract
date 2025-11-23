from django.db import transaction
from rest_framework import serializers
from uuid import UUID
import re

from blog.models import BaseBlogModel
from blog.models import (
    # Journey models
    MicroJourneyBlog, ShortEssayJourneyBlog, ArticleJourneyBlog,
    # Successful experience models
    MicroSuccessfulExperience, ShortEssaySuccessfulExperience, ArticleSuccessfulExperience,
    # Milestone models  
    MicroMilestoneJourneyBlog, ShortEssayMilestoneJourneyBlog, ArticleMilestoneJourneyBlog,
    # Report insight models
    report_insight_micro, report_insight_short_essay, report_insight_article,
    # Consumption models
    MicroConsumption, ShortEssayConsumption, ArticleConsumption,
    # Answering question models
    MicroAnsweringQuestionBlog, ShortEssayAnsweringQuestionBlog, ArticleAnsweringQuestionBlog,
    # Failed initiation models
    MicroFailedInitiationExperience, ShortEssayFailedInitiationExperience, ArticleFailedInitiationExperience
)


class BlogCreationService:
    """Service for handling blog creation with validation and type-specific logic"""
    
    BLOG_TYPES = [
        'journey', 'successful_experience', 'milestone',
        'report_insight', 'failed_initiation', 'consumption', 'answering_question'
    ]

    CONTENT_TYPES = ['micro', 'short_essay', 'article']
    
    def __init__(self, validated_data):
        self.validated_data = validated_data
        self.blog_type = validated_data['type']
        self.content_type = validated_data['content_type']
    
    def validate_data(self):
        """Comprehensive validation of blog creation data"""
        errors = {}
        
        # Content validation
        if self.blog_type != 'failed_initiation' and not self.validated_data.get('content'):
            errors['content'] = "Content is required for this blog type"
        
        # Type-specific field validation
        type_validation_map = {
            'journey': self._validate_journey,
            'successful_experience': self._validate_successful_experience,
            'milestone': self._validate_milestone,
            'report_insight': self._validate_report_insight,
            'consumption': self._validate_consumption,
            'answering_question': self._validate_answering_question,
            'failed_initiation': self._validate_failed_initiation
        }
        
        validator = type_validation_map.get(self.blog_type)
        if validator:
            type_errors = validator()
            if type_errors:
                errors.update(type_errors)
        
        # UUID validation
        uuid_fields = ['milestone_id', 'contribution']
        for field in uuid_fields:
            if self.validated_data.get(field):
                try:
                    UUID(self.validated_data[field])
                except ValueError:
                    errors[field] = f"{field} must be a valid UUID"
        
        if errors:
            raise serializers.ValidationError(errors)
    
    def _validate_journey(self):
        errors = {}
        if not self.validated_data.get('target_user'):
            errors['target_user'] = "target_user is required for journey blogs"
        return errors
    
    def _validate_successful_experience(self):
        errors = {}
        if not self.validated_data.get('target_user'):
            errors['target_user'] = "target_user is required for successful experience blogs"
        return errors
    
    def _validate_milestone(self):
        errors = {}
        if not self.validated_data.get('milestone_id'):
            errors['milestone_id'] = "milestone_id is required for milestone blogs"
        if not self.validated_data.get('target_user'):
            errors['target_user'] = "target_user is required for milestone blogs"
        return errors
    
    def _validate_report_insight(self):
        errors = {}
        if not self.validated_data.get('report_type') or not self.validated_data.get('report_id'):
            errors['report'] = "report_type and report_id are required for report insights"
        return errors
    
    def _validate_consumption(self):
        errors = {}
        if not self.validated_data.get('url') or not self.validated_data.get('contribution'):
            errors['consumption'] = "url and contribution are required for consumption blogs"
        return errors
    
    def _validate_answering_question(self):
        errors = {}
        if not self.validated_data.get('questionid'):
            errors['questionid'] = "questionid is required for answering questions"
        return errors
    
    def _validate_failed_initiation(self):
        errors = {}
        if not self.validated_data.get('failure_reason') or not self.validated_data.get('target_details'):
            errors['failed_initiation'] = "failure_reason and target_details are required for failed initiations"
        return errors
    
    @transaction.atomic
    def create_blog(self):
        """Create blog with proper transaction handling"""
        self.validate_data()
        
        blog_type = self.blog_type
        content_type = self.content_type
        content = self.validated_data.get('content')
        userid = self.validated_data.get('userid')

        # Create base blog
        base_blog = BaseBlogModel.objects.create(
            userid=userid,
            type=f"{blog_type}_{content_type}"
        )

        # Create concrete blog based on type
        blog_creators = {
            'journey': self._create_journey_blog,
            'successful_experience': self._create_successful_experience_blog,
            'milestone': self._create_milestone_blog,
            'report_insight': self._create_report_insight_blog,
            'consumption': self._create_consumption_blog,
            'answering_question': self._create_answering_question_blog,
            'failed_initiation': self._create_failed_initiation_blog
        }

        creator = blog_creators.get(blog_type)
        if not creator:
            raise serializers.ValidationError(f"Unsupported blog type: {blog_type}")

        concrete_blog = creator(base_blog, content)
        return concrete_blog
    
    def _create_journey_blog(self, base_blog, content):
        model_map = {
            'micro': MicroJourneyBlog,
            'short_essay': ShortEssayJourneyBlog,
            'article': ArticleJourneyBlog
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            target_user=self.validated_data['target_user'],
            content=content
        )
    
    def _create_successful_experience_blog(self, base_blog, content):
        model_map = {
            'micro': MicroSuccessfulExperience,
            'short_essay': ShortEssaySuccessfulExperience,
            'article': ArticleSuccessfulExperience
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            target_user=self.validated_data['target_user'],
            content=content
        )
    
    def _create_milestone_blog(self, base_blog, content):
        model_map = {
            'micro': MicroMilestoneJourneyBlog,
            'short_essay': ShortEssayMilestoneJourneyBlog,
            'article': ArticleMilestoneJourneyBlog
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            target_user=self.validated_data['target_user'],
            milestone_id=self.validated_data['milestone_id'],
            content=content
        )
    
    def _create_report_insight_blog(self, base_blog, content):
        model_map = {
            'micro': report_insight_micro,
            'short_essay': report_insight_short_essay,
            'article': report_insight_article
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            report_type=self.validated_data['report_type'],
            report_id=self.validated_data['report_id'],
            content=content
        )
    
    def _create_consumption_blog(self, base_blog, content):
        model_map = {
            'micro': MicroConsumption,
            'short_essay': ShortEssayConsumption,
            'article': ArticleConsumption
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            url=self.validated_data['url'],
            contribution=self.validated_data['contribution'],
            content=content
        )
    
    def _create_answering_question_blog(self, base_blog, content):
        model_map = {
            'micro': MicroAnsweringQuestionBlog,
            'short_essay': ShortEssayAnsweringQuestionBlog,
            'article': ArticleAnsweringQuestionBlog
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            questionid=self.validated_data['questionid'],
            content=content
        )
    
    def _create_failed_initiation_blog(self, base_blog, content):
        model_map = {
            'micro': MicroFailedInitiationExperience,
            'short_essay': ShortEssayFailedInitiationExperience,
            'article': ArticleFailedInitiationExperience
        }
        return model_map[self.content_type].objects.create(
            id=base_blog.id,
            country_id=self.validated_data.get('country_id'),
            state_id=self.validated_data.get('state_id'),
            district_id=self.validated_data.get('district_id'),
            subdistrict_id=self.validated_data.get('subdistrict_id'),
            village_id=self.validated_data.get('village_id'),
            target_details=self.validated_data['target_details'],
            failure_reason=self.validated_data['failure_reason'],
            content=content
        )