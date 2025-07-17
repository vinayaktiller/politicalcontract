from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

class UserGroupParticipation(models.Model):
    user_id = models.BigIntegerField(
        primary_key=True,
        help_text="Unique user ID"
    )
    
    groups_as_speaker = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="Array of group IDs where user participates as speaker"
    )
    
    groups_as_member = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="Array of group IDs where user participates as member"
    )
    
    groups_as_agent = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="Array of group IDs where user participates as outside agent"
    )
    
    groups_as_founder = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="Array of group IDs where user is the founder"
    )
    
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event"."user_group_participation'
        
    def __str__(self):
        return f"Participation for user {self.user_id}"