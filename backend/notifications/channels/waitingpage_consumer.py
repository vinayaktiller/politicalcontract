
import logging
import re
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from pendingusers.models.notifications import InitiationNotification
from pendingusers.services.pending_user_service import verify_and_transfer_user
from users.models import UserTree


logger = logging.getLogger(__name__)


class WaitingpageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer to manage the waiting page.
    Sends initiation status updates and handles verification/rejection.
    """

    async def connect(self):
        self.user_email = self.scope["url_route"]["kwargs"]["user_email"]
        sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', self.user_email)
        self.group_name = f"waiting_{sanitized_email}"

        logger.info(f"User connected: {self.user_email}, Group: {self.group_name}")

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        notification = await self.get_latest_notification(self.user_email)
        if notification:
            await self.send(text_data=json.dumps({
                "type": "initial_notification",
                "notification_id": notification.id,
                "status": notification.status,
                "message": InitiationNotification.STATUS_MESSAGES.get(notification.status, "Waiting for update..."),
                "user_email": self.user_email,
            }))
        else:
            logger.info(f"No pending notification found for {self.user_email}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"User disconnected: {self.user_email}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            user_email = data.get("user_email", "unknown_user")
            notification_id = data.get("notificationId")

            logger.info(f"Received message from {user_email}: {data}")

            exists = await self.notification_exists(notification_id)
            if not exists:
                logger.warning(f"Notification with ID {notification_id} not found.")
                return

            if message_type == "accept_verification":
                petitioner = await self.verify_user(notification_id)
                if petitioner:
                    user_tree = await self.get_user_tree(petitioner.id)
                    name = user_tree.name
                    profile_pic = user_tree.profilepic.url if user_tree.profilepic else None

                    await self.send(text_data=json.dumps({
                        "type": "verification_success",
                        "user_email": user_email,
                        "generated_user_id": petitioner.id,
                        "name": name,
                        "profile_pic": profile_pic
                    }))
                else:
                    logger.error(f"Verification failed for notification {notification_id}")

            elif message_type == "accept_rejection":
                await self.move_notification_to_archive(notification_id)
                logger.info(f"User {user_email} accepted rejection for notification {notification_id}")

            else:
                logger.warning(f"Unknown message type received: {message_type}")

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message.")

    async def waitingpage_message(self, event):
        await self.send(text_data=json.dumps({
            "user_email": self.user_email,
            "status": event.get("status", "unknown"),
            "message": event.get("message", ""),
            "notification_id": event.get("notification_id"),
        }))

    @database_sync_to_async
    def get_latest_notification(self, email):
        try:
            return InitiationNotification.objects.filter(applicant__gmail=email).order_by("-created_at").first()
        except Exception as e:
            logger.error(f"Error fetching latest notification for {email}: {str(e)}")
            return None

    @database_sync_to_async
    def notification_exists(self, notification_id):
        return InitiationNotification.objects.filter(id=notification_id).exists()

    @database_sync_to_async
    def verify_user(self, notification_id):
        try:
            notification = (
                InitiationNotification.objects
                .select_related('applicant')
                .get(id=notification_id)
            )
            # mark_as_completed deletes notification & applicant, returns petitioner
            petitioner = notification.mark_as_completed()
            return petitioner
        except Exception as e:
            logger.error(f"Error verifying user for notification {notification_id}: {str(e)}")
            return None

    @database_sync_to_async
    def get_user_tree(self, petitioner_id):
        return UserTree.objects.get(id=petitioner_id)

    @database_sync_to_async
    def move_notification_to_archive(self, notification_id):
        try:
            notification = InitiationNotification.objects.get(id=notification_id)
            notification.move_to_archive()
        except ObjectDoesNotExist:
            logger.warning(f"Notification {notification_id} does not exist.")
        except Exception as e:
            logger.error(f"Error moving notification {notification_id} to archive: {str(e)}")
