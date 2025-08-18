from django.db import models
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
from .journeyblog import JourneyBlog

import uuid

class MilestoneJourneyBlog(JourneyBlog):
    """
    Abstract base class for Journey Blogs that are tied to a Milestone.
    """
    milestone_id = models.UUIDField()
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
    class Meta:
        db_table = 'blog"."milestone_journey_blog_micro'  # Changed

class ShortEssayMilestoneJourneyBlog(MilestoneJourneyBlog, ShortEssayContent):
    class Meta:
        db_table = 'blog"."milestone_journey_blog_short_essay'  # Changed

class ArticleMilestoneJourneyBlog(MilestoneJourneyBlog, ArticleContent):
    class Meta:
        db_table = 'blog"."milestone_journey_blog_article'  # Changed