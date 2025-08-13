# users/models.py
from django.db import models
import logging
from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid


logger = logging.getLogger(__name__)

class Milestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Using UUID instead of BigAutoField
    """Model to store user achievements and milestones"""
    user_id = models.BigIntegerField()
    title = models.CharField(max_length=255)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    photo_id = models.BigIntegerField(null=True, blank=True)
    photo_url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'userschema"."milestone'
        indexes = [
            models.Index(fields=['user_id']),
        ]

    
    def save(self, *args, **kwargs):
        """Override save to send notification when new Milestone is created."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from .petitioners import Petitioner
            user= Petitioner.objects.get(id=self.user_id)
            if user.is_online:
                self.send_milestone_notification()
                logger.info(f"Milestone notification sent for {self.title} to user {self.user_id}")
               
           

    def send_milestone_notification(self):
        """Send milestone notification via WebSocket."""
        
        try:
            logger.info(f"3 Sending milestone notification for {self.title} to user {self.user_id}")
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user_id}"
            notification_data = {
                "notification": {
                    "notification_type": "Milestone_Notification",
                    "notification_message": f"Achievement unlocked: {self.title} for {self.type}",
                    "notification_data": {
                        "milestone_id": str(self.id),
                        "user_id": self.user_id,
                        "title": self.title,
                        "text": self.text,
                        "created_at": self.created_at.isoformat(),
                        "delivered": self.delivered,
                        "photo_id": self.photo_id,
                        "photo_url": self.photo_url,
                        "type": self.type,
                    },
                    "notification_number": str(self.id),
                    "notification_freshness": True,
                    "created_at": self.created_at.isoformat(),
                }
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification.message",
                    **notification_data
                }
            )
            logger.info(f"  34 Milestone notification sent for {self.title} to group {group_name}")

            # Mark as delivered and save
            self.delivered = True
            self.save(update_fields=['delivered'])
            logger.info(f"21 Milestone {self.id} delivered to user {self.user_id}")

        except Exception as e:
            logger.error(f"Error sending milestone notification: {str(e)}")