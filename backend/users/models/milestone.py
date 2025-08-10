# users/models.py
from django.db import models, transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import uuid

logger = logging.getLogger(__name__)

class Milestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID primary key
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
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            # transaction.on_commit(self.send_milestone_notification)
            self.send_milestone_notification()

    def send_milestone_notification(self):
        """Send milestone notification via WebSocket."""
        logger.error(f"Sending milestone notification for {self.title} to user {self.user_id}")
        try:
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user_id}"

            notification = {
                 
                    "notification_type": "Milestone_Notification",
                    "notification_message": f"Achievement unlocked: {self.title} for {self.type}",
                    "notification_data": {
                        "milestone_id": str(self.id),  # Ensure UUID is string
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

            event_data = {
                "notification": notification,
            }

            # # Send over WebSocket
            # async_to_sync(channel_layer.group_send)(
            #     group_name,
            #     {
            #         "type": "notification.message",
            #         "notification": notification,
            #     }
            # )

            async_to_sync(channel_layer.group_send)(
                f"notifications_{notification.connection_id}",
                event_data
                
            )

            # Mark as delivered and save
            self.delivered = True
            super().save(update_fields=['delivered'])
            logger.info(f"Milestone  delivered to user {self.user_id}")

        except Exception as e:
            logger.error(f"Error sending milestone notification: {str(e)}")
