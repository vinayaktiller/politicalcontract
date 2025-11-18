# serializers.py
from rest_framework import serializers

from ..models import (
    MicroJourneyBlog, 
    ShortEssayJourneyBlog, 
    ArticleJourneyBlog,
    BaseBlogModel
)
from users.models import Circle, UserTree
from users.profilepic_manager.utils import get_profilepic_url

class UserSummarySerializer(serializers.ModelSerializer):
    profilepic_url = serializers.SerializerMethodField()

    class Meta:
        model = UserTree
        fields = ['id', 'name', 'profilepic_url']

    def get_profilepic_url(self, obj):
        request = self.context.get('request')
        return get_profilepic_url(obj, request)

    # def get_profilepic_url(self, obj):
    #     if obj.profilepic:
    #         request = self.context.get('request')
    #         return request.build_absolute_uri(obj.profilepic.url) if request else obj.profilepic.url
    #     return None

class BaseBlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseBlogModel
        fields = [
            'id', 'userid', 'likes', 'dislikes',
            'relevant_count', 'irrelevant_count',
            'shares', 'type', 'created_at', 'updated_at'
        ]

class JourneyBlogSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    target_user = serializers.IntegerField(required=True)
    content = serializers.CharField(required=True)
    type = serializers.ChoiceField(
        choices=['micro', 'short_essay', 'article'],
        write_only=True,
        required=True
    )
    
    # Response fields
    base_blog = serializers.SerializerMethodField()
    userid_details = serializers.SerializerMethodField()
    target_user_details = serializers.SerializerMethodField()
    my_journey = serializers.SerializerMethodField()
    blog_type = serializers.SerializerMethodField()

    def get_base_blog(self, obj):
        try:
            base_blog = BaseBlogModel.objects.get(id=obj.id)
            return BaseBlogSerializer(base_blog, context=self.context).data
        except BaseBlogModel.DoesNotExist:
            return None

    def get_userid_details(self, obj):
        try:
            base_blog = BaseBlogModel.objects.get(id=obj.id)
            usertree = UserTree.objects.get(id=base_blog.userid)
            return UserSummarySerializer(usertree, context=self.context).data
        except (BaseBlogModel.DoesNotExist, UserTree.DoesNotExist):
            return None

    def get_target_user_details(self, obj):
        request_user_id = self.context.get('userid')
        if request_user_id == obj.target_user:
            return {"is_self": True, "message": "This is my journey"}
        else:
            try:
                usertree = UserTree.objects.get(id=obj.target_user)
                return UserSummarySerializer(usertree, context=self.context).data
            except UserTree.DoesNotExist:
                return None

    def get_my_journey(self, obj):
        return self.context.get('userid') == obj.target_user

    def get_blog_type(self, obj):
        if isinstance(obj, MicroJourneyBlog):
            return "micro_journey_blog"
        elif isinstance(obj, ShortEssayJourneyBlog):
            return "short_essay_journey_blog"
        return "article_journey_blog"

    def validate(self, data):
        request_user_id = self.context.get('userid')
        target_user_id = data.get('target_user')

        if request_user_id == target_user_id:
            return data

        relation_exists = Circle.objects.filter(
            userid=request_user_id,
            otherperson=target_user_id
        ).exists() or Circle.objects.filter(
            userid=target_user_id,
            otherperson=request_user_id
        ).exists()

        if not relation_exists:
            raise serializers.ValidationError("No relation exists between the users.")
        return data

    def create(self, validated_data):
        blog_type = validated_data.pop('type')
        content = validated_data.get('content')
        
        if blog_type == 'micro':
            return MicroJourneyBlog.objects.create(content=content, **validated_data)
        elif blog_type == 'short_essay':
            return ShortEssayJourneyBlog.objects.create(content=content, **validated_data)
        return ArticleJourneyBlog.objects.create(content=content, **validated_data)

    def update(self, instance, validated_data):
        # Prevent changing blog type after creation
        validated_data.pop('type', None)
        
        instance.target_user = validated_data.get('target_user', instance.target_user)
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance