from django.db import models
from geographies.models.geos import Country, State, District, Subdistrict, Village
from .eventname import EventName
from users.models.usertree import UserTree
from .event import Event

class EventParticipationProfile(models.Model):
    user = models.ForeignKey(UserTree, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    is_speaker = models.BooleanField(default=False)
    is_organizer = models.BooleanField(default=False)
    is_agent = models.BooleanField(default=False)
    is_participant = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_member = models.BooleanField(default=False)

    # Self-reference: the agent must also be an EventParticipationProfile instance
    agent_profile = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members_brought'
    )

    class Meta:
        unique_together = ('user', 'event')

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.is_member:
            if any([self.is_speaker, self.is_organizer, self.is_agent, self.is_participant]):
                raise ValidationError("A member cannot hold any other roles.")
            if not self.agent_profile:
                raise ValidationError("A member must have an agent profile linked.")
            if self.agent_profile.event != self.event:
                raise ValidationError("Agent must belong to the same event.")
        if self.agent_profile == self:
            raise ValidationError("User cannot be their own agent.")

    def __str__(self):
        return f"{self.user} @ {self.event}"
    class Meta:
        db_table = 'event"."eventprofiles'
