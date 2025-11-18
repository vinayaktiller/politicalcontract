import logging
import re
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db import transaction
from pendingusers.models.notifications import InitiationNotification
from pendingusers.models import PendingVerificationNotification, PendingUser, NoInitiatorUser
from users.models import UserTree
from notifications.login_push.services.push_notifications import handle_user_notifications_on_login

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

        # Check if this is a no-initiator user and send current status
        no_initiator_status = await self.get_no_initiator_status(self.user_email)
        if no_initiator_status:
            await self.send_no_initiator_status(no_initiator_status)
        else:
            # Regular flow - check for pending verification notifications
            pending_notifications = await self.get_pending_notifications(self.user_email)
            for notification in pending_notifications:
                await self.send(text_data=json.dumps({
                    "type": "admin_verification",
                    "status": "pending_verification",
                    "message": "🎉 Your account has been approved! Click to complete verification.",
                    "pending_user_id": notification.pending_user_id,
                    "user_email": self.user_email,
                }))
                
                # Mark notification as delivered
                await self.mark_notification_delivered(notification.id)

            # Check for regular initiation notifications
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
            pending_user_id = data.get("pending_user_id")

            logger.info(f"Received message from {user_email}: {data}")

            # Check if this is a no-initiator user
            is_no_initiator = await self.check_no_initiator(user_email)
            
            if is_no_initiator:
                # Handle no-initiator specific messages
                if message_type == "accept_no_initiator_verification":
                    await self.handle_accept_no_initiator_verification(user_email, pending_user_id)
                elif message_type == "accept_no_initiator_rejection":
                    await self.handle_accept_no_initiator_rejection(user_email, pending_user_id)
                else:
                    logger.warning(f"Unknown message type for no-initiator user: {message_type}")
            else:
                # Handle regular initiator flow
                notification_id = data.get("notificationId")
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

    async def send_no_initiator_status(self, status_data):
        """Send the current no-initiator status to the client"""
        await self.send(text_data=json.dumps({
            "type": "no_initiator_status",
            "status": status_data["status"],
            "message": status_data["message"],
            "user_email": self.user_email,
            "pending_user_id": status_data["pending_user_id"],
            "rejection_reason": status_data.get("rejection_reason", ""),
            "claimed_by_name": status_data.get("claimed_by_name", ""),
        }))

    async def handle_accept_no_initiator_verification(self, user_email, pending_user_id):
        """Handle when no-initiator user accepts verification"""
        try:
            # Perform the actual verification and transfer
            petitioner, user_tree = await self.perform_no_initiator_verification(user_email, pending_user_id)
            
            if petitioner and user_tree:
                # Send success response
                await self.send(text_data=json.dumps({
                    "type": "verification_success",
                    "user_email": user_email,
                    "generated_user_id": petitioner.id,
                    "name": user_tree.name,
                    "profile_pic": user_tree.profilepic.url if user_tree.profilepic else None,
                    "message": "Verification completed successfully"
                }))
                
                # Clean up pending user data
                success = await self.cleanup_no_initiator_user(user_email)
                if success:
                    logger.info(f"No-initiator verification completed and cleanup done for {user_email}")
                    # Send cleanup success message
                    await self.send(text_data=json.dumps({
                        "type": "no_initiator_cleanup_success",
                        "user_email": user_email,
                        "message": "Cleanup completed successfully"
                    }))
                else:
                    logger.error(f"No-initiator verification cleanup failed for {user_email}")
            else:
                await self.send(text_data=json.dumps({
                    "type": "no_initiator_verification_failed",
                    "user_email": user_email,
                    "message": "Verification failed. Please contact support."
                }))
                logger.error(f"No-initiator verification failed for {user_email}")

        except Exception as e:
            logger.error(f"Error in handle_accept_no_initiator_verification: {str(e)}")
            await self.send(text_data=json.dumps({
                "type": "no_initiator_verification_failed",
                "user_email": user_email,
                "message": "Verification failed due to server error."
            }))

    async def handle_accept_no_initiator_rejection(self, user_email, pending_user_id):
        """Handle when no-initiator user accepts rejection"""
        # Perform cleanup - delete pending user and no initiator data
        success = await self.cleanup_no_initiator_user(user_email)
        
        if success:
            await self.send(text_data=json.dumps({
                "type": "no_initiator_rejection_cleanup_success",
                "user_email": user_email,
                "message": "Rejection accepted and data cleaned up"
            }))
            logger.info(f"No-initiator rejection cleanup completed for {user_email}")
        else:
            await self.send(text_data=json.dumps({
                "type": "no_initiator_rejection_cleanup_failed", 
                "user_email": user_email,
                "message": "Cleanup failed. Please contact support."
            }))
            logger.error(f"No-initiator rejection cleanup failed for {user_email}")

    @database_sync_to_async
    def perform_no_initiator_verification(self, user_email, pending_user_id):
        """Perform the actual verification and transfer for no-initiator user"""
        try:
            with transaction.atomic():
                # Get the pending user
                pending_user = PendingUser.objects.select_for_update().get(gmail=user_email, id=pending_user_id)
                
                # Get the NoInitiatorUser to find who verified it
                no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
                if not no_initiator_data or no_initiator_data.verified_by is None:
                    logger.error(f"No verified_by found for pending user {user_email}")
                    return None, None

                # Set initiator and event type for verification
                pending_user.initiator_id = no_initiator_data.verified_by.id
                pending_user.event_type = 'online'
                pending_user.save()

                # Verify and transfer (returns Petitioner)
                petitioner = pending_user.verify_and_transfer()

                # Get the corresponding UserTree
                user_tree = UserTree.objects.get(id=petitioner.id)

                return petitioner, user_tree
                
        except Exception as e:
            logger.error(f"Error in perform_no_initiator_verification: {str(e)}")
            return None, None

    @database_sync_to_async
    def get_no_initiator_status(self, user_email):
        """Get the current status of a no-initiator user"""
        try:
            pending_user = PendingUser.objects.get(gmail=user_email, initiator_id__isnull=True)
            no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
            
            if not no_initiator_data:
                return None

            status_info = {
                "pending_user_id": pending_user.id,
                "status": no_initiator_data.verification_status,
                "rejection_reason": "",
                "claimed_by_name": ""
            }

            # Set appropriate message based on status
            if no_initiator_data.verification_status == "unclaimed":
                status_info["message"] = "⏳ Your application is awaiting review by our team."
            elif no_initiator_data.verification_status == "claimed":
                status_info["message"] = "👀 Your application is currently being reviewed by an admin."
                if no_initiator_data.claimed_by:
                    status_info["claimed_by_name"] = no_initiator_data.claimed_by.name
            elif no_initiator_data.verification_status == "verified":
                status_info["message"] = "🎉 Your account has been verified! Click OK to complete the process."
            elif no_initiator_data.verification_status == "rejected":
                status_info["message"] = "❌ Your application has been rejected."
                # Extract rejection reason from notes if available
                if no_initiator_data.notes and "Reason:" in no_initiator_data.notes:
                    try:
                        reason_part = no_initiator_data.notes.split("Reason:")[1].strip()
                        status_info["rejection_reason"] = reason_part
                    except:
                        status_info["rejection_reason"] = "No reason provided"
                else:
                    status_info["rejection_reason"] = "No reason provided"
            else:
                status_info["message"] = "⏳ Your application is being processed."

            return status_info

        except PendingUser.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting no-initiator status for {user_email}: {str(e)}")
            return None

    async def waitingpage_message(self, event):
        await self.send(text_data=json.dumps({
            "user_email": self.user_email,
            "status": event.get("status", "unknown"),
            "message": event.get("message", ""),
            "notification_id": event.get("notification_id"),
        }))
        
    async def admin_verification_message(self, event):
        """Handle admin verification messages - both verification and rejection"""
        message_data = event["message"]
        
        await self.send(text_data=json.dumps({
            "type": "admin_verification",
            "user_email": self.user_email,
            "status": message_data.get("status", "unknown"),
            "message": message_data.get("message", ""),
            "pending_user_id": message_data.get("pending_user_id"),
            "rejection_reason": message_data.get("rejection_reason", ""),
        }))

    # Keep all your existing database_sync_to_async methods
    @database_sync_to_async
    def mark_user_online(self, user_email, is_online):
        """Mark user as online or offline in cache"""
        cache.set(f"user_online_{user_email}", is_online, timeout=300)

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

    @database_sync_to_async
    def cleanup_no_initiator_user(self, user_email):
        """Clean up no-initiator user data after verification/rejection acceptance"""
        try:
            pending_user = PendingUser.objects.get(gmail=user_email)
            no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
            
            if no_initiator_data:
                no_initiator_data.delete()
            
            pending_user.delete()
            return True
        except PendingUser.DoesNotExist:
            logger.warning(f"PendingUser with email {user_email} does not exist for cleanup")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up no-initiator user {user_email}: {str(e)}")
            return False