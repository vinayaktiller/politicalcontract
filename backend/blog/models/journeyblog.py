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
        db_table = 'blog"."micro_journey_blog'


class ShortEssayJourneyBlog(JourneyBlog, ShortEssayContent):
    class Meta:
        db_table = 'blog"."short_essay_journey_blog'


class ArticleJourneyBlog(JourneyBlog, ArticleContent):
    class Meta:
        db_table = 'blog"."article_journey_blog'


