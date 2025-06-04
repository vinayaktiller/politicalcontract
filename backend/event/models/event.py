from django.db import models
from geographies.models.geos import Country, State, District, Subdistrict, Village
from .eventname import EventName
from users.models.usertree import UserTree
class Event(models.Model):
    MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    eventname = models.ForeignKey(EventName, on_delete=models.DO_NOTHING)
    event_title = models.CharField(max_length=255, help_text="Specific title for this particular instance of the event")

    eventid = models.BigIntegerField(null=True, blank=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='offline')

    # For online events
    participation_link = models.URLField(null=True, blank=True)

    # For offline events
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True)
    address_details = models.TextField(null=True, blank=True)

    eventdate = models.DateTimeField(null=True, blank=True)
    information = models.TextField(null=True, blank=True)

    # Optional media
    photos = models.ImageField(upload_to='event_photos/', null=True, blank=True)
    post_event_related_links = models.URLField(null=True, blank=True) #like youtube link, etc.

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_title or f"{self.eventname.name} ({self.eventdate.strftime('%Y-%m-%d') if self.eventdate else 'No Date'})"
    class Meta:
        db_table = 'event"."event'
