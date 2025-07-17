import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from notifications.channels_handlers.initiation_notification_handler import handle_initiation_notification
from notifications.channels_handlers.connection_notification_handler import handle_connection_notification
from notifications.channels_handlers.connection_status_handler import handle_connection_status
from notifications.channels_handlers.speaker_invitation_handler import handle_speaker_invitation

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for handling real-time notifications."""

    async def connect(self):
        """Handles WebSocket connection."""
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"notifications_{self.user_id}"
        logger.info(f"User {self.user_id} connected to WebSocket.")

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"User {self.user_id} disconnected from WebSocket.")

    async def receive(self, text_data):
        """Handles incoming WebSocket messages and delegates processing."""
        try:
            data = json.loads(text_data)
            notification_type = data.get("notificationType")
            
            if notification_type == "Initiation_Notification":
                await handle_initiation_notification(self, data)
            elif notification_type == "Connection_Notification":
                await handle_connection_notification(self, data)
            elif notification_type == "Connection_Status":
                await handle_connection_status(self, data)
            elif notification_type == "Group_Speaker_Invitation":
                await handle_speaker_invitation(self, data)

            else:
                raise ValueError(f"Unknown notification type: {notification_type}")

        except json.JSONDecodeError:
            logger.error(f"JSON decoding error from user {self.user_id}: {text_data}")
            await self.send(json.dumps({"error": "Invalid JSON format"}))

    async def notification_message(self, event):
        """Sends notifications to the WebSocket client."""
        logger.info(f"Sending notification to user {self.user_id}: {event}")
        await self.send(text_data=json.dumps(event))
