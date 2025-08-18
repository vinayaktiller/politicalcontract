from django.db import models
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
import uuid

class JourneyBlog(models.Model):
    """Abstract base for all journey-related blogs."""
    id = models.UUIDField(primary_key=True)  # Same as BaseBlogModel.id
    target_user = models.BigIntegerField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_self_journey(self):
        from .Baseblogmodel import BaseBlogModel
        try:
            base_blog = BaseBlogModel.objects.get(id=self.id)
            return base_blog.userid == self.target_user
        except BaseBlogModel.DoesNotExist:
            return False

class MicroJourneyBlog(JourneyBlog, MicroContent):
    class Meta:
        db_table = 'blog"."journey_blog_micro'  # Changed

class ShortEssayJourneyBlog(JourneyBlog, ShortEssayContent):
    class Meta:
        db_table = 'blog"."journey_blog_short_essay'  # Changed

class ArticleJourneyBlog(JourneyBlog, ArticleContent):
    class Meta:
        db_table = 'blog"."journey_blog_article'  # Changed

