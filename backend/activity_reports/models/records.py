from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from users.models import Petitioner
from datetime import date
import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class UserMonthlyActivity(models.Model):
    """Stores daily activity in a compact monthly format"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        Petitioner, 
        on_delete=models.CASCADE,
        related_name='monthly_activities'
    )
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()  # 1-12
    active_days = ArrayField(
        models.PositiveSmallIntegerField(),  # Stores day numbers (1-31)
        default=list
    )
    
    class Meta:
        db_table = 'activity_reports"."user_monthly_activity'
        unique_together = [('user', 'year', 'month')]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'year', 'month'],
                name='unique_user_monthly_activity'
            )
        ]
    
    def __str__(self):
        return f"{self.user} - {self.year}/{self.month}"

class DailyActivitySummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    active_users = ArrayField(
        models.BigIntegerField(),
        default=list
    )
    
    class Meta:
        db_table = 'activity_reports"."daily_activity_summary'
    
    def __str__(self):
        return f"Activity on {self.date}"

# # Signal to send updates on save
# @receiver(post_save, sender=DailyActivitySummary)
# def send_activity_update(sender, instance, **kwargs):
#     today = date.today()
#     if instance.date == today:  # Only send updates for today
#         channel_layer = get_channel_layer()
#         print(f"Sending activity update for {instance.date} with {len(instance.active_users)} active users")
#         async_to_sync(channel_layer.group_send)(
#             "activity_today",  # Fixed group name
#             {
#                 "type": "activity_update",
#                 "count": len(instance.active_users)
#             }
#         )