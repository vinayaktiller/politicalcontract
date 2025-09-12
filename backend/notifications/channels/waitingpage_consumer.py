# consumers.py
import logging
import re
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from pendingusers.models.notifications import InitiationNotification
from pendingusers.models import PendingVerificationNotification
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

        # Mark user as online
        await self.mark_user_online(self.user_email, True)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Check for pending verification notifications
        pending_notifications = await self.get_pending_notifications(self.user_email)
        for notification in pending_notifications:
            await self.send(text_data=json.dumps({
                "type": "admin_verification",
                "status": "verified",
                "message": "🎉 Congratulations! Your account has been verified by our team.",
                "generated_user_id": notification.generated_user_id,
                "name": notification.name,
                "profile_pic": notification.profile_pic or "",
                "user_email": self.user_email,
            }))
            
            # Mark notification as delivered
            await self.mark_notification_delivered(notification.id)

        # Check if this is a no-initiator user
        is_no_initiator = await self.check_no_initiator(self.user_email)
        
        if is_no_initiator:
            await self.send(text_data=json.dumps({
                "type": "no_initiator_status",
                "status": "admin_review",
                "message": "Your application is under review by our team.",
                "user_email": self.user_email,
            }))
        else:
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
        # Mark user as offline
        await self.mark_user_online(self.user_email, False)
        
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"User disconnected: {self.user_email}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            user_email = data.get("user_email", "unknown_user")
            notification_id = data.get("notificationId")

            logger.info(f"Received message from {user_email}: {data}")

            # Check if this is a no-initiator user
            is_no_initiator = await self.check_no_initiator(user_email)
            
            if is_no_initiator:
                # Handle no-initiator specific messages
                if message_type == "admin_verification_success":
                    await self.handle_admin_verification_success(user_email, data)
                else:
                    logger.warning(f"Unknown message type for no-initiator user: {message_type}")
            else:
                # Handle regular initiator flow
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
                            "profile_pic": profile_pic or ""
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
        
    async def admin_verification_message(self, event):
        """Handle admin verification messages for no-initiator users"""
        # Extract message from event (it's now a dict, not a string)
        message_data = event["message"]
        
        await self.send(text_data=json.dumps({
            "type": "admin_verification",
            "user_email": self.user_email,
            "status": message_data.get("status", "unknown"),
            "message": message_data.get("message", ""),
            "generated_user_id": message_data.get("generated_user_id"),
            "name": message_data.get("name"),
            "profile_pic": message_data.get("profile_pic", ""),
        }))

    @database_sync_to_async
    def mark_user_online(self, user_email, is_online):
        """Mark user as online or offline in cache"""
        cache.set(f"user_online_{user_email}", is_online, timeout=300)  # 5 minute timeout

    @database_sync_to_async
    def get_pending_notifications(self, user_email):
        """Get pending verification notifications for a user"""
        return list(PendingVerificationNotification.objects.filter(
            user_email=user_email, 
            delivered=False
        ))

    @database_sync_to_async
    def mark_notification_delivered(self, notification_id):
        """Mark a notification as delivered"""
        try:
            notification = PendingVerificationNotification.objects.get(id=notification_id)
            notification.delivered = True
            notification.save()
        except PendingVerificationNotification.DoesNotExist:
            logger.warning(f"Pending notification {notification_id} does not exist.")

    @database_sync_to_async
    def check_no_initiator(self, email):
        """Check if a user is a no-initiator user"""
        from pendingusers.models import PendingUser
        try:
            pending_user = PendingUser.objects.get(gmail=email)
            return pending_user.initiator_id is None
        except PendingUser.DoesNotExist:
            return False

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
        try:
            return UserTree.objects.get(id=petitioner_id)
        except UserTree.DoesNotExist:
            logger.error(f"UserTree with id {petitioner_id} does not exist")
            return None

    @database_sync_to_async
    def move_notification_to_archive(self, notification_id):
        try:
            notification = InitiationNotification.objects.get(id=notification_id)
            notification.move_to_archive()
        except ObjectDoesNotExist:
            logger.warning(f"Notification {notification_id} does not exist.")
        except Exception as e:
            logger.error(f"Error moving notification {notification_id} to archive: {str(e)}")
            
    async def handle_admin_verification_success(self, user_email, data):
        """Handle admin verification success for no-initiator users"""
        # Store user data in local storage
        generated_user_id = data.get("generated_user_id")
        name = data.get("name")
        profile_pic = data.get("profile_pic")
        
        if generated_user_id:
            await self.send(text_data=json.dumps({
                "type": "admin_verification_success",
                "user_email": user_email,
                "generated_user_id": generated_user_id,
                "name": name,
                "profile_pic": profile_pic or ""
            }))