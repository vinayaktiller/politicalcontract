from django.db import models

class EventName(models.Model):
    EventName = models.CharField(max_length=255, unique=True)
    Owner= models.ForeignKey('users.usertree', on_delete=models.CASCADE, null=True, blank=True)
    Eventsymbol = models.ImageField(upload_to='event_photos/', null=True, blank=True)

    class Meta:
        db_table = 'userschema"."eventname'  # Schema-aware table name