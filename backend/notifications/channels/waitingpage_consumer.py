# import json
# import logging
# import re
# import asyncio
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from asgiref.sync import sync_to_async
# from pendingusers.models import PendingUser, InitiationNotification

# # Configure Django logger
# logger = logging.getLogger(__name__)

# # Utility functions to handle database operations asynchronously
# @sync_to_async
# def get_notification(user_email):
#     return InitiationNotification.objects.get(applicant__gmail=user_email)

# @sync_to_async
# def mark_notification_completed(notification):
#     notification.mark_as_completed()

# @sync_to_async
# def mark_notification_completed_for_verification(notification):
#     notification.mark_as_completed_for_verification()

# @sync_to_async
# def get_pending_user(user_email):
#     return PendingUser.objects.get(gmail=user_email)

# @sync_to_async
# def verify_pending_user(pending_user):
#     pending_user.is_verified = True
#     pending_user.verify_and_transfer()

# class WaitingpageConsumer(AsyncWebsocketConsumer):
#     """
#     WebSocket consumer for handling waiting page notifications.

#     - Manages WebSocket connections for applicants.
#     - Sends initiation notifications upon connection.
#     - Processes user responses like verification and rejection.
#     """

#     async def connect(self):
#         """
#         Handles WebSocket connection establishment.

#         - Extracts and sanitizes user email to generate a valid group name.
#         - Adds the connection to a channel group.
#         - Fetches and sends initiation notification.
#         """
#         self.user_email = self.scope["url_route"]["kwargs"]["user_email"]
#         sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', self.user_email)
#         self.group_name = f"waiting_{sanitized_email}"
        
#         logger.info(f"User connected: {self.user_email}, Group: {self.group_name}")

#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )
#         await self.accept()

#         try:
#             notification = await get_notification(self.user_email)
#             logger.info(f"Fetched notification for {self.user_email}: {notification}")
#             await asyncio.to_thread(notification.send_websocket_notification)
#         except InitiationNotification.DoesNotExist:
#             logger.warning(f"No initiation notification found for {self.user_email}")

#     async def disconnect(self, close_code):
#         """
#         Handles WebSocket disconnection.

#         - Removes the user from the channel group.
#         - Logs the disconnection status.
#         """
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
#         logger.info(f"User disconnected: {self.user_email}")

#     async def receive(self, text_data):
#         """
#         Processes incoming WebSocket messages.

#         - Parses JSON messages sent by the client.
#         - Handles verification or rejection actions.
#         - Updates initiation notification status in the database.

#         :param text_data: JSON-formatted WebSocket message.
#         """
#         try:
#             data = json.loads(text_data)
#             logger.info(f"Received message from {self.user_email}: {data}")

#             if data.get("type") == "accept_rejection":
#                 notification = await get_notification(self.user_email)
#                 await mark_notification_completed(notification)
#                 logger.info(f"Notification marked as completed for {self.user_email}")

#             elif data.get("type") == "accept_verification":
#                 notification = await get_notification(self.user_email)
#                 await mark_notification_completed_for_verification(notification)

#                 pending_user = await get_pending_user(self.user_email)
#                 await verify_pending_user(pending_user)

#                 logger.info(f"User {self.user_email} has been verified and transferred.")
                
#             else:
#                 logger.warning(f"Unknown message type received: {data.get('type')}")

#         except json.JSONDecodeError:
#             logger.error(f"Invalid JSON format received from {self.user_email}: {text_data}")
#         except InitiationNotification.DoesNotExist:
#             logger.warning(f"Notification does not exist for {self.user_email}")
#         except PendingUser.DoesNotExist:
#             logger.warning(f"Pending user not found for {self.user_email}")

#     async def waitingpage_message(self, event):
#         """
#         Sends the same notification message received in the event to the WebSocket client.

#         - Uses the `notification` data from the event.
#         - Logs and sends the full notification object instead of breaking it into separate keys.

#         :param event: Dictionary containing the notification data.
#         """
#         notification = event.get("notification", {})

#         logger.info(f"Forwarding WebSocket notification for {self.user_email}: {notification}")

#         await self.send(text_data=json.dumps(notification))
# import logging
# import re
# import json

# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from django.core.exceptions import ObjectDoesNotExist

# from pendingusers.models.notifications import InitiationNotification
# from pendingusers.services.pending_user_service import verify_and_transfer_user

# logger = logging.getLogger(__name__)

# class WaitingpageConsumer(AsyncWebsocketConsumer):
#     """
#     WebSocket consumer for handling basic connections, messages, and disconnections.
#     """

#     async def connect(self):
#         self.user_email = self.scope["url_route"]["kwargs"]["user_email"]
#         sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', self.user_email)
#         self.group_name = f"waiting_{sanitized_email}"

#         logger.info(f"User connected: {self.user_email}, Group: {self.group_name}")

#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)
#         logger.info(f"User disconnected: {self.user_email}")
    
#     async def receive(self, text_data):
#         """
#         Handles messages from the WebSocket client.

#         Expects JSON:
#             {
#               "type": "accept_verification" | "accept_rejection",
#               "user_email": "...",
#               "notificationId": 123
#             }
#         """
#         try:
#             data = json.loads(text_data)
#             message_type = data.get("type")
#             user_email = data.get("user_email", "unknown_user")
#             notification_id = data.get("notificationId")
#             logger.info(f"Received message from {user_email}: {data}")

#             # First, make sure the notification exists
#             exists = await self.notification_exists(notification_id)
#             if not exists:
#                 logger.warning(f"Notification with ID {notification_id} not found.")
#                 return

#             if message_type == "accept_verification":
#                 petitioner = await self.verify_user(notification_id)
#                 if petitioner:
#                     await self.send(text_data=json.dumps({
#                         "type": "verification_success",
#                         "user_email": user_email,
#                         "generated_user_id": petitioner.id
#                     }))
#                 else:
#                     logger.error(f"Verification failed for notification")

#             elif message_type == "accept_rejection":
#                 await self.move_notification_to_archive(notification_id)
#                 logger.info(f"User {user_email} accepted rejection for notification {notification_id}")

#             else:
#                 logger.warning(f"Unknown message type received: {message_type}")

#         except json.JSONDecodeError:
#             logger.error("Failed to decode JSON message.")

#     async def waitingpage_message(self, event):
#         """
#         Handler for messages sent via channel_layer.group_send().
#         """
#         await self.send(text_data=json.dumps({
#             "user_email": event.get("user_email", "unknown_user"),
#             "status": event.get("status", "unknown"),
#             "message": event.get("message", ""),
#             "notification_id": event.get("notification_id"),
#         }))
#         logger.info(f"Message sent to {event.get('user_email')}: {event.get('message')}")

#     @database_sync_to_async
#     def notification_exists(self, notification_id):
#         """
#         Quick existence check to avoid unnecessary fetches.
#         """
#         return InitiationNotification.objects.filter(id=notification_id).exists()

#     @database_sync_to_async
#     def verify_user(self, notification_id):
#         """
#         Fetches the notification *and* its related applicant in a sync thread,
#         then calls the synchronous verify_and_transfer_user().
#         """
#         try:
#             notification = (
#                 InitiationNotification.objects
#                 .select_related('applicant')
#                 .get(id=notification_id)
#             )
#             return verify_and_transfer_user(notification.applicant)
#         except ObjectDoesNotExist:
#             return None

#     @database_sync_to_async
#     def move_notification_to_archive(self, notification_id):
#         """
#         Fetches and archives the notification in a sync thread.
#         """
#         try:
#             notification = InitiationNotification.objects.get(id=notification_id)
#             notification.move_to_archive()
#         except ObjectDoesNotExist:
#             pass


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
