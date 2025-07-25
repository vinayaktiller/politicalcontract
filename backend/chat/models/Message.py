from django.db import models
from django.core.exceptions import ValidationError
import uuid
from .Conversation import Conversation
from users.models import Petitioner
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
        db_table = 'chat"."message'
        indexes = [
            models.Index(fields=['receiver', 'delivered']),
            models.Index(fields=['receiver', 'read']),
        ]

    def clean(self):
        # Verify sender and receiver are conversation participants
        participants = [self.conversation.participant1_id, self.conversation.participant2_id]
        if self.sender_id not in participants or self.receiver_id not in participants:
            raise ValidationError("Sender and receiver must be conversation participants")
        if self.sender_id == self.receiver_id:
            raise ValidationError("Sender and receiver cannot be the same")

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # Set receiver automatically
        if is_new and not self.receiver_id:
            if self.sender == self.conversation.participant1:
                self.receiver = self.conversation.participant2
            else:
                self.receiver = self.conversation.participant1
        
        # Run validation first
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update conversation's last message if this is a new message
        if is_new:
            self.conversation.update_last_message(self)
            # Try to deliver the message
            self.try_deliver()

    def try_deliver(self):
        """Attempt to deliver the message if receiver is online"""
        try:
            if self.receiver.is_online:
                self.send_delivery_notification()
            else:
                logger.info(f"Receiver {self.receiver.id} is offline. Message will be delivered when online.")
        except Exception as e:
            logger.error(f"Error in try_deliver: {str(e)}")

    def send_delivery_notification(self):
        """Notify receiver and sender about delivery status"""
        try:
            channel_layer = get_channel_layer()
            
            # Notify receiver about new message
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
                    "timestamp": self.timestamp.isoformat()
                }
            )
            
            # Notify sender about delivery status
            sender_group = f"notifications_{self.sender.id}"
            async_to_sync(channel_layer.group_send)(
                sender_group,
                {
                    "type": "notification_message",
                    "category": "chat_system",
                    "subtype": "message_delivered",
                    "message_id": str(self.id),
                    "conversation_id": str(self.conversation_id),
                    "delivered": True,
                    "timestamp": timezone.now().isoformat()
                }
            )
            
            # Update delivery status in database
            self.delivered = True
            self.save(update_fields=['delivered'])
            
        except Exception as e:
            logger.error(f"Failed to send delivery notification: {str(e)}")

    def mark_as_read(self):
        """Mark message as read and notify sender"""
        if not self.read:
            self.read = True
            self.save(update_fields=['read'])
            self.send_read_notification()

    def send_read_notification(self):
        """Notify sender that message has been read"""
        try:
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.sender.id}"
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification_message",
                    "category": "chat_system",
                    "subtype": "message_read",
                    "message_id": str(self.id),
                    "conversation_id": str(self.conversation_id),
                    "read": True,
                    "timestamp": timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to send read notification: {str(e)}")

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"