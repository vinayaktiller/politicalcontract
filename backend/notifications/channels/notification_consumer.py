# src/features/notifications/consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q

# Import your notification/chat handlers
from notifications.channels_handlers.initiation_notification_handler import handle_initiation_notification
from notifications.channels_handlers.connection_notification_handler import handle_connection_notification
from notifications.channels_handlers.connection_status_handler import handle_connection_status
from notifications.channels_handlers.speaker_invitation_handler import handle_speaker_invitation
from notifications.channels_handlers.chat_system_handler import handle_chat_system
from notifications.channels_handlers.milestone_handler import handle_milestone_notification  # <- milestone handler import

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for handling real-time notifications and chat events."""

    async def connect(self):
        """Handles WebSocket connection."""
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"notifications_{self.user_id}"
        logger.info(f"User {self.user_id} connected to WebSocket.")

        # Add to notification group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Mark user as online
        await self.mark_user_online(True)

        # Fetch undelivered messages
        await self.fetch_undelivered_messages()

        # Fetch undelivered milestones (milestone integration)
        await self.fetch_undelivered_milestones()

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"User {self.user_id} disconnected from WebSocket.")

        # Mark user as offline
        await self.mark_user_online(False)

    async def mark_user_online(self, online):
        """Update user's online status and notify connections."""
        try:
            from users.models import Petitioner
            user = await sync_to_async(Petitioner.objects.get)(id=self.user_id)
            user.is_online = online
            await sync_to_async(user.save)(update_fields=['is_online'])

            # Notify user's connections about status change
            await self.notify_connection_status(online)
        except Exception as e:
            logger.error(f"Error updating online status: {str(e)}")

    async def notify_connection_status(self, online):
        """Notify user's connections about online/offline status change."""
        try:
            from users.models import Circle
            connections = await sync_to_async(list)(
                Circle.objects.filter(
                    Q(userid=self.user_id) | Q(otherperson=self.user_id)
                ).distinct()
            )
            for connection in connections:
                other_id = (
                    connection.userid if str(connection.userid) != str(self.user_id)
                    else connection.otherperson
                )
                group_name = f"notifications_{other_id}"

                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "notification_message",
                        "category": "connection_status",
                        "user_id": self.user_id,
                        "online": online,
                        "timestamp": timezone.now().isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Error notifying connection status: {str(e)}")

    async def fetch_undelivered_messages(self):
        """Fetch undelivered messages for the user."""
        try:
            # The frontend chat system handler is expected to process this request.
            await self.send(json.dumps({
                "category": "chat_system",
                "action": "fetch_undelivered"
            }))
        except Exception as e:
            logger.error(f"Error fetching undelivered messages: {str(e)}")

    # New milestone fetching method
    async def fetch_undelivered_milestones(self):
        """Fetch undelivered milestones for the user"""
        try:
            from users.models import Milestone  # avoid circular import

            milestones = await sync_to_async(list)(
                Milestone.objects.filter(user_id=self.user_id, delivered=False)
            )
            for milestone in milestones:
                await self.send_milestone_notification(milestone)

                milestone.delivered = True
                await sync_to_async(milestone.save)(update_fields=['delivered'])
        except Exception as e:
            logger.error(f"Error fetching undelivered milestones: {str(e)}")

    async def send_milestone_notification(self, milestone):
        """Send milestone notification to client"""
        notification = {
            "notification_type": "Milestone_Notification",
            "notification_message": f"Achievement unlocked: {milestone.title}",
            "notification_data": {
                "milestone_id": str(milestone.id),  # Ensure UUID is string milestone.id,
                "user_id": milestone.user_id,
                "title": milestone.title,
                "text": milestone.text,
                "created_at": milestone.created_at.isoformat(),
                "delivered": milestone.delivered,
                "photo_id": milestone.photo_id,
                "photo_url": milestone.photo_url,
                "type": milestone.type
            },
            "notification_number":str(milestone.id) ,
            "notification_freshness": True,
            "created_at": milestone.created_at.isoformat()
        }
        
        await self.send(json.dumps({
            "notification": notification
        }))

    async def receive(self, text_data):
        """Handles incoming WebSocket messages and delegates processing."""
        try:
            data = json.loads(text_data)
            category = data.get("category")

            # Handle milestone notifications (integrated)
            if category == "milestone":
                await handle_milestone_notification(self, data)

            # Handle chat system events
            elif category == "chat_system":
                await handle_chat_system(self, data)

            # Handle message status update category separately
            elif category == "message_status_update":
                await self.handle_message_status_update(data)

            # Other notification types
            elif data.get("notificationType") == "Initiation_Notification":
                await handle_initiation_notification(self, data)
            elif data.get("notificationType") == "Connection_Notification":
                await handle_connection_notification(self, data)
            elif data.get("notificationType") == "Connection_Status":
                await handle_connection_status(self, data)
            elif data.get("notificationType") == "Group_Speaker_Invitation":
                await handle_speaker_invitation(self, data)
            else:
                raise ValueError(f"Unknown message category: {category or 'no category'}")

        except json.JSONDecodeError:
            logger.error(f"JSON decoding error from user {self.user_id}: {text_data}")
            await self.send(json.dumps({
                "error": "Invalid JSON format",
                "category": "error"
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(json.dumps({
                "error": str(e),
                "category": "error",
                "source": "receive_handler"
            }))

    async def handle_message_status_update(self, data):
        """Handle client-side message status updates."""
        try:
            message_id = data.get("message_id")
            new_status = data.get("status")

            valid_statuses = ['sent', 'delivered', 'delivered_update', 'read', 'read_update']
            if new_status not in valid_statuses:
                raise ValueError("Invalid message status")

            await handle_chat_system(self, {
                "action": "update_message_status",
                "message_id": message_id,
                "status": new_status,
                "category": "chat_system"
            })

        except Exception as e:
            logger.error(f"Status update handling error: {str(e)}")
            await self.send(json.dumps({
                "status": "error",
                "category": "message_status_update",
                "message": str(e)
            }))

    async def notification_message(self, event):
        """Sends notifications to the WebSocket client with category filtering."""
        event.setdefault('category', 'general')

        logger.info(f"Sending notification to user {self.user_id}: {event}")
        await self.send(text_data=json.dumps(event))
