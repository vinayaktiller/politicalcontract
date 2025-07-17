from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from geographies.models.geos import Country, State, District, Subdistrict, Village

class Group(models.Model):
    name = models.CharField(max_length=255)
    founder = models.BigIntegerField ()
    
    profile_pic = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL for the group's main profile picture"
    )
    
    speakers = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for group speakers"
    )

    members = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for group members"
    )
    
    outside_agents = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for outside agents associated with the group"
    )

    # Address fields
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True)

    institution = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Institution or organization associated with the group"
    )

    links = ArrayField(
        models.URLField(max_length=500),
        blank=True,
        default=list,
        help_text="List of URLs associated with the group"
    )

    photos = ArrayField(
        models.URLField(max_length=500),
        blank=True,
        default=list,
        help_text="List of URLs for group photos"
    )

    pending_speakers = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for pending speakers"
    )

    # Automatic timestamps
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name
    def add_speaker(self, user_id):
        """Add speaker and update UserGroupParticipation"""
        if user_id not in self.speakers:
            self.speakers.append(user_id)
            self.save(update_fields=['speakers'])
            
            # Update or create participation record
            from .UserGroupParticipation import UserGroupParticipation
            participation, created = UserGroupParticipation.objects.get_or_create(user_id=user_id)
            if self.id not in participation.groups_as_speaker:
                participation.groups_as_speaker.append(self.id)
                participation.save(update_fields=['groups_as_speaker'])

    class Meta:
        db_table = 'event"."group'  # Schema-aware table name