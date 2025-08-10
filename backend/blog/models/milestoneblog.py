from django.db import models
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
from .journeyblog import JourneyBlog

import uuid


class MilestoneJourneyBlog(JourneyBlog):
    """
    Abstract base class for Journey Blogs that are tied to a Milestone.
    """
    milestone_id = models.UUIDField(null=True, blank=True)
    class Meta:
        abstract = True

    
    def is_target_same_as_user(self):
        from users.models import Milestone
        """
        Checks if the milestone's target_user_id is the same as its user_id.
        """
        if not self.milestone_id:
            return False
        
        try:
            milestone = Milestone.objects.get(id=self.milestone_id)
        except Milestone.DoesNotExist:
            return False
        
        return milestone.target_user == milestone.user_id


class MicroMilestoneJourneyBlog(MilestoneJourneyBlog, MicroContent):
    """Micro journey blog tied to a milestone."""
    class Meta:
        db_table = 'blog"."micro_milestone_journey_blog'


class ShortEssayMilestoneJourneyBlog(MilestoneJourneyBlog, ShortEssayContent):
    """Short essay journey blog tied to a milestone."""
    class Meta:
        db_table = 'blog"."short_essay_milestone_journey_blog'


class ArticleMilestoneJourneyBlog(MilestoneJourneyBlog, ArticleContent):
    """Article journey blog tied to a milestone."""
    class Meta:
        db_table = 'blog"."article_milestone_journey_blog'
