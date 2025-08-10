from django.db import models
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
from django.core.exceptions import ValidationError
from .journeyblog import JourneyBlog

import uuid

class SuccessfulExperienceBlog(JourneyBlog):
    class Meta:
        abstract = True
        unique_together = ('userid', 'target_user')
    def clean(self):
        """
        Enforces only one instance per user-target pair.
        """
        if self.userid is None or self.target_user is None:
            raise ValidationError("Both userid and target_user must be set.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
class MicroSuccessfulExperience(SuccessfulExperienceBlog, MicroContent):
    """
    Successful Experience in micro format.
    """
    class Meta(SuccessfulExperienceBlog.Meta):
        db_table = 'blog"."micro_successful_experience'


class ShortEssaySuccessfulExperience(SuccessfulExperienceBlog, ShortEssayContent):
    """
    Successful Experience in short essay format.
    """
    class Meta(SuccessfulExperienceBlog.Meta):
        db_table = 'blog"."short_essay_successful_experience'


class ArticleSuccessfulExperience(SuccessfulExperienceBlog, ArticleContent):
    """
    Successful Experience in article format.
    """
    class Meta(SuccessfulExperienceBlog.Meta):
        db_table = 'blog"."article_successful_experience'