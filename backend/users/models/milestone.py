from django.db import models
import logging
from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid

logger = logging.getLogger(__name__)

class Milestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    """Model to store user achievements and milestones"""
    user_id = models.BigIntegerField()
    title = models.CharField(max_length=255)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)  # Backend only - set by WebSocket consumer
    completed = models.BooleanField(default=False)  # Backend only - set by completion API
    photo_id = models.BigIntegerField(null=True, blank=True)
    photo_url = models.URLField(max_length=500, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'userschema"."milestone'
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['delivered', 'completed']),
        ]

    @property
    def status(self):
        """Get the milestone status based on delivered and completed flags"""
        if not self.delivered and not self.completed:
            return "pending"  # Stage 1: Not delivered yet
        elif self.delivered and not self.completed:
            return "delivered"  # Stage 2: Delivered but not acknowledged
        elif self.delivered and self.completed:
            return "completed"  # Stage 3: Fully processed
        else:
            return "invalid"

    def save(self, *args, **kwargs):
        """Override save to send notification when new Milestone is created."""
        is_new = self._state.adding
        
        # Validate state transition
        if not is_new:
            old_instance = Milestone.objects.get(pk=self.pk)
            # Prevent invalid state: completed cannot be True without delivered being True
            if self.completed and not self.delivered:
                raise ValueError("Cannot mark as completed without being delivered")
        
        super().save(*args, **kwargs)
        
        if is_new:
            from .petitioners import Petitioner
            try:
                user = Petitioner.objects.get(id=self.user_id)
                if user.is_online:
                    # User is online, send immediately via WebSocket
                    self.send_milestone_notification()
                    logger.info(f"Milestone notification sent for {self.title} to user {self.user_id}")
                else:
                    # User is offline, milestone will be sent when they connect
                    logger.info(f"User {self.user_id} is offline, milestone {self.id} saved with delivered=False")
            except Petitioner.DoesNotExist:
                logger.error(f"User {self.user_id} not found when saving milestone {self.id}")

    def send_milestone_notification(self):
        """Send milestone notification via WebSocket when user is online."""
        try:
            logger.info(f"Sending milestone notification for {self.title} to user {self.user_id}")
            
            # CRITICAL: Only send if delivered is False AND completed is False
            if self.delivered or self.completed:
                logger.warning(f"Milestone {self.id} already delivered or completed, skipping notification")
                return
                
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user_id}"
            
            # Send notification WITHOUT completed field
            notification_data = {
                "notification": {
                    "notification_type": "Milestone_Notification",
                    "notification_message": f"Achievement unlocked: {self.title} for {self.type}",
                    "notification_data": {
                        "milestone_id": str(self.id),
                        "user_id": self.user_id,
                        "title": self.title,
                        "text": self.text,
                        'delivered': self.delivered,  # Send delivered status
                        "created_at": self.created_at.isoformat(),
                        "photo_id": self.photo_id,
                        "photo_url": self.photo_url,
                        "type": self.type,
                        # DO NOT INCLUDE completed field
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
            logger.info(f"Milestone notification sent for {self.title} to group {group_name}")
            
            # CONSUMER RULE: Update delivered to True after sending notification
            self.delivered = True
            self.save(update_fields=['delivered'])
            logger.info(f"Milestone {self.id} marked as delivered=True")
            
        except Exception as e:
            logger.error(f"Error sending milestone notification: {str(e)}")

    def mark_as_completed(self):
        """Mark milestone as completed (acknowledged by user) via API only"""
        if not self.delivered:
            raise ValueError("Cannot complete undelivered milestone")
        
        # NOTIFICATION BAR CLICK RULE: Only update completed, not delivered
        self.completed = True
        self.save(update_fields=['completed'])
        logger.info(f"Milestone {self.id} marked as completed for user {self.user_id}")
        return self
    def send_milestone_notification_stage_2(self):
        """Send milestone notification via WebSocket when user is online."""
        try:
            logger.info(f"Sending milestone notification for {self.title} to user {self.user_id}")
            
            
                
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user_id}"
            
            # Send notification WITHOUT completed field
            notification_data = {
                "notification": {
                    "notification_type": "Milestone_Notification",
                    "notification_message": f"Achievement unlocked: {self.title} for {self.type}",
                    "notification_data": {
                        "milestone_id": str(self.id),
                        "user_id": self.user_id,
                        "title": self.title,
                        "text": self.text,
                        'delivered': self.delivered,  # Send delivered status
                        "created_at": self.created_at.isoformat(),
                        "photo_id": self.photo_id,
                        "photo_url": self.photo_url,
                        "type": self.type,
                        # DO NOT INCLUDE completed field
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
            logger.info(f"Milestone notification sent for {self.title} to group {group_name}")
            
            # CONSUMER RULE: Update delivered to True after sending notification
            self.delivered = True
            self.save(update_fields=['delivered'])
            logger.info(f"Milestone {self.id} marked as delivered=True")
            
        except Exception as e:
            logger.error(f"Error sending milestone notification: {str(e)}")