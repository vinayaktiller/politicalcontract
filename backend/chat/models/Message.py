from django.db import models
from django.core.exceptions import ValidationError
import uuid
from .Conversation import Conversation
from users.models import Petitioner, UserTree
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

class Message(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('delivered_update', 'Delivered Update'),
        ('read', 'Read'),
        ('read_update', 'Read Update'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    last_status_update = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['timestamp']
        db_table = 'chat"."message'  # Note: double quotes mean this is for PostgreSQL!
        indexes = [
            models.Index(fields=['receiver', 'status']),
        ]

    def clean(self):
        # Verify sender and receiver are conversation participants and not the same person
        participants = [self.conversation.participant1_id, self.conversation.participant2_id]
        if self.sender_id not in participants or self.receiver_id not in participants:
            raise ValidationError("Sender and receiver must be conversation participants")
        if self.sender_id == self.receiver_id:
            raise ValidationError("Sender and receiver cannot be the same")

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Set receiver automatically if creating a new message and receiver is not provided
        if is_new and not self.receiver_id:
            if self.sender == self.conversation.participant1:
                self.receiver = self.conversation.participant2
            else:
                self.receiver = self.conversation.participant1

        # Run validation before save
        self.full_clean()
        super().save(*args, **kwargs)

        if is_new:
            # Update conversation last message
            self.conversation.update_last_message(self)
            # Try delivery and notify if possible
            self.try_deliver()

    def update_status(self, new_status):
        """Update message status and trigger notifications"""
        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status', 'last_status_update'])
            self.notify_status_change()

    def notify_status_change(self):
        """Notify sender about status changes"""
        try:
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.sender.id}"

            payload = {
                "type": "notification_message",
                "category": "chat_system",
                "message_id": str(self.id),
                "conversation_id": str(self.conversation_id),
                "status": self.status,
            }

            if self.status == 'delivered':
                payload["subtype"] = "message_delivered"
            elif self.status == 'delivered_update':
                payload["subtype"] = "message_delivered_update"
            elif self.status == 'read':
                payload["subtype"] = "message_read"
            elif self.status == 'read_update':
                payload["subtype"] = "message_read_update"
            else:
                return  # Only notify for the above states

            async_to_sync(channel_layer.group_send)(group_name, payload)

        except Exception as e:
            logger.error(f"Failed to send status notification: {str(e)}")

    def try_deliver(self):
        """Attempt to deliver the message if receiver is online."""
        try:
            if getattr(self.receiver, 'is_online', False):
                self.update_status('delivered')
                self.send_new_message_notification()
            else:
                logger.info(
                    f"Receiver {self.receiver.id} is offline. Message {self.id} will be delivered when online."
                )
                # Stay in 'sent' status
        except Exception as e:
            logger.error(f"Error in try_deliver: {str(e)}")

    def send_new_message_notification(self):
        """Notify receiver about a new message using UserTree for sender details"""
        try:
            # Get UserTree for sender
            try:
                sender_tree = UserTree.objects.get(id=self.sender_id)
                sender_name = sender_tree.name
                sender_profile = (
                    f"http://127.0.0.1:8000{sender_tree.profilepic.url}" 
                    if sender_tree.profilepic 
                    else None
                )
            except UserTree.DoesNotExist:
                # Fallback to Petitioner data if UserTree missing
                sender_name = f"{self.sender.first_name} {self.sender.last_name}"
                sender_profile = None

            channel_layer = get_channel_layer()
            receiver_group = f"notifications_{self.receiver.id}"
            async_to_sync(channel_layer.group_send)(
                receiver_group,
                {
                    "type": "notification_message",
                    "category": "chat_system",
                    "subtype": "new_message",
                    "message_id": str(self.id),
                    "conversation_id": str(self.conversation_id),
                    "content": self.content,
                    "sender_id": str(self.sender_id),
                    "timestamp": self.timestamp.isoformat(),
                    "status": self.status,
                    "sender_name": sender_name,
                    "sender_profile": sender_profile,
                }
            )
        except Exception as e:
            logger.error(f"Failed to notify receiver of new message: {str(e)}")

    def mark_as_read(self):
        """Mark message as read and update status"""
        if self.status not in ['read', 'read_update']:
            # Upgrade to 'read_update' if sender is online
            if getattr(self.sender, 'is_online', False):
                self.update_status('read_update')
            else:
                self.update_status('read')

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"

