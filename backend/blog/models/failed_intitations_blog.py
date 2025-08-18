from django.db import models
from .Baseblogmodel import BaseBlogModel
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
from geographies.models.geos import Country, State, District, Subdistrict, Village  # Import your geo models
import uuid

class BaseFailedInitiationExperience(models.Model):
    id = models.UUIDField(primary_key=True)  # Same as BaseBlogModel.id
    # Geographic fields (optional)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Person/group details
    target_details = models.TextField(
        blank=True, 
        null=True,
        help_text="Details about the person or group where initiation failed"
    )
    
    # Failure reason
    failure_reason = models.TextField(
        blank=True, 
        null=True,
        help_text="Reason for the initiation failure"
    )

    class Meta:
        abstract = True
class MicroFailedInitiationExperience(BaseFailedInitiationExperience, MicroContent):
    class Meta:
        db_table = 'blog"."failed_initiation_experience_micro'  # Changed
class ShortEssayFailedInitiationExperience(BaseFailedInitiationExperience, ShortEssayContent):
    class Meta:
        db_table = 'blog"."failed_initiation_experience_short_essay'  # Changed
class ArticleFailedInitiationExperience(BaseFailedInitiationExperience, ArticleContent):
    class Meta:
        db_table = 'blog"."failed_initiation_experience_article'  # Changed
        
