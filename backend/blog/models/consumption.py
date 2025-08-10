from django.db import models
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
import uuid

class consumption(models.Model):
    id = models.UUIDField(primary_key=True)  # Same as BaseBlogModel.id
    url= models.URLField(max_length=400, null=True, blank=True, unique=True)  # URL of the consumed content
    contribution = models.UUIDField()  # Same as BaseBlogModel.id
    class Meta:
        abstract = True

class MicroConsumption(consumption, MicroContent):
    """Micro consumption of content."""
    class Meta:
        db_table = 'blog"."consumption_micro'

class ShortEssayConsumption(consumption, ShortEssayContent):
    """Short essay consumption of content."""
    class Meta:
        db_table = 'blog"."consumption_short_essay'

class ArticleConsumption(consumption, ArticleContent):
    """Article consumption of content."""
    class Meta:
        db_table = 'blog"."consumption_article'

