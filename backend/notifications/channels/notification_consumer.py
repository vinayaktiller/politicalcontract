import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from notifications.channels_handlers.initiation_notification_handler import handle_initiation_notification
from notifications.channels_handlers.connection_notification_handler import handle_connection_notification
from notifications.channels_handlers.connection_status_handler import handle_connection_status
from notifications.channels_handlers.speaker_invitation_handler import handle_speaker_invitation
from notifications.channels_handlers.chat_system_handler import handle_chat_system  # New import
from django.utils import timezone
from django.db.models import Q
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

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"User {self.user_id} disconnected from WebSocket.")

        # Mark user as offline
        await self.mark_user_online(False)

    async def mark_user_online(self, online):
        """Update user's online status"""
        try:
            from users.models import Petitioner
            user = await sync_to_async(Petitioner.objects.get)(id=self.user_id)
            user.is_online = online
            await sync_to_async(user.save)(update_fields=['is_online'])

            # Notify connections about status change
            await self.notify_connection_status(online)
        except Exception as e:
            logger.error(f"Error updating online status: {str(e)}")

    async def notify_connection_status(self, online):
        """Notify user's connections about status change"""
        try:
            from users.models import Circle
            connections = await sync_to_async(list)(
                Circle.objects.filter(
                    Q(userid=self.user_id) | Q(otherperson=self.user_id)
                ).distinct()
            )

            for connection in connections:
                other_id = connection.userid if connection.userid != self.user_id else connection.otherperson
                group_name = f"notifications_{other_id}"

                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "notification_message",
                        "category": "connection_status",
                        "user_id": self.user_id,
                        "online": online,
                        "timestamp": timezone.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error notifying connection status: {str(e)}")

    async def fetch_undelivered_messages(self):
        """Fetch undelivered messages for the user"""
        try:
            # Request undelivered messages
            await self.send(json.dumps({
                "category": "chat_system",
                "action": "fetch_undelivered"
            }))
        except Exception as e:
            logger.error(f"Error fetching undelivered messages: {str(e)}")

    async def receive(self, text_data):
        """Handles incoming WebSocket messages and delegates processing."""
        try:
            data = json.loads(text_data)
            category = data.get("category")

            # Handle chat system events
            if category == "chat_system":
                await handle_chat_system(self, data)
            # Handle other notification types
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

    async def notification_message(self, event):
        """Sends notifications to the WebSocket client with category filtering."""
        # Add category information to the event
        event.setdefault('category', 'general')

        logger.info(f"Sending notification to user {self.user_id}: {event}")
        await self.send(text_data=json.dumps(event))