from django.db import models, transaction
from django.utils.timezone import now
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import re
import logging
import threading
from users.models.petitioners import Petitioner
from .pendinguser import PendingUser
import traceback

logger = logging.getLogger(__name__)

class InitiationNotification(models.Model):
    class Status(models.TextChoices):
        INITIATOR_OFFLINE = "initiator_offline", "Initiator Offline"
        SENT = "sent", "Sent"
        NOT_VIEWED = "not_viewed", "Not Viewed"
        REACTED_PENDING = "reacted_pending", "Reacted Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    STATUS_MESSAGES = {
        Status.INITIATOR_OFFLINE: "⚠️ Your initiator is currently offline...",
        Status.SENT: "✅ Your initiation request has been sent...",
        Status.NOT_VIEWED: "👀 Your initiation request has been sent...",
        Status.REACTED_PENDING: "⏳ Your initiator has seen your initiation request...",
        Status.VERIFIED: "🎉 Congratulations! Your initiator has verified...",
        Status.REJECTED: "🚫 Your initiation request has been rejected..."
    }

    initiator = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name="initiated_notifications")
    applicant = models.ForeignKey(PendingUser, on_delete=models.CASCADE, related_name="received_notifications")
    status = models.CharField(max_length=20, choices=Status.choices, default=None, null=True, blank=True)
    sent = models.BooleanField(default=False)
    viewed = models.BooleanField(default=False)
    reacted = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pendinguser"."initiationnotification'
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["applicant", "status"]),
        ]

    def __str__(self):
        return f"Notification from {self.initiator} to {self.applicant} - Status: {self.status}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs) 

        if is_new:
            if self.initiator.is_online:
                self.process_notification()
            else:
                self._set_offline_status()

    def process_notification(self):
        from pendingusers.services.send_notification_to_initiator import send_notification_to_initiator

        send_notification_to_initiator(self)
        self.sent = True
        self.status = self.Status.SENT
        self.save(update_fields=["sent", "status"])
        self.mark_as_not_viewed()

    def update_status(self, new_status):
        if self.status == new_status:
            return
        self.status = new_status
        self.save(update_fields=["status"])
        self.send_websocket_notification()
        logger.info(f"Notification {self.id} status updated to {new_status}")

    def send_websocket_notification(self):
        try:
            channel_layer = get_channel_layer()
            sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', self.applicant.gmail)
            group_name = f"waiting_{sanitized_email}"

            message = self.STATUS_MESSAGES.get(self.status, "Unknown status update.")
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "waitingpage_message",
                    "notification_id": self.id,
                    "status": self.status,
                    "message": message
                }
            )
        except Exception as e:
            logger.error(f"WebSocket notification failed: {str(e)}")

    def _set_offline_status(self):
        try:
            self.refresh_from_db()
            if not self.sent:
                self.update_status(self.Status.INITIATOR_OFFLINE)
        except InitiationNotification.DoesNotExist:
            logger.warning("Notification deleted before offline status could be set")

    def mark_as_not_viewed(self):
        threading.Timer(30, self._safely_set_not_viewed_status).start()

    def _safely_set_not_viewed_status(self):
        try:
            with transaction.atomic():
                # Refresh and lock the database row
                fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)
                if not fresh_instance.viewed:
                    fresh_instance.update_status(self.Status.NOT_VIEWED)
        except InitiationNotification.DoesNotExist:
            logger.info("Notification deleted before not-viewed status could be set")

    def mark_as_viewed(self):
        try:
            with transaction.atomic():
                fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)
                fresh_instance.viewed = True
                fresh_instance.save(update_fields=["viewed"])
                fresh_instance.mark_as_reacted_pending()
        except InitiationNotification.DoesNotExist:
            logger.warning("Notification deleted before viewed status could be set")

    def mark_as_reacted_pending(self):
        threading.Timer(30, self._safely_set_reacted_pending_status).start()

    def _safely_set_reacted_pending_status(self):
        try:
            with transaction.atomic():
                fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)
                if not fresh_instance.reacted:
                    fresh_instance.update_status(self.Status.REACTED_PENDING)
        except InitiationNotification.DoesNotExist:
            logger.info("Notification deleted before reacted-pending status could be set")

    def mark_as_verified(self):
        with transaction.atomic():
            fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)
            fresh_instance.reacted = True
            fresh_instance.save(update_fields=["reacted"])
            fresh_instance.update_status(self.Status.VERIFIED)
            
            return fresh_instance.applicant.verify_and_transfer()

    def mark_as_rejected(self):
        with transaction.atomic():
            fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)
            fresh_instance.reacted = True
            fresh_instance.save(update_fields=["reacted"])
            fresh_instance.update_status(self.Status.REJECTED)

    def mark_as_completed(self):
        from pendingusers.models import PendingUser  # Import if not already at top
        from users.models.petitioners import Petitioner

        with transaction.atomic():
            # Lock and refresh the current notification instance
            fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)

            # Mark as completed
            fresh_instance.completed = True
            fresh_instance.save(update_fields=["completed"])

            # Get applicant and corresponding petitioner (if any)
            applicant = fresh_instance.applicant
            petitioner = None

            if applicant:
                try:
                    petitioner = Petitioner.objects.get(gmail=applicant.gmail)
                except Petitioner.DoesNotExist:
                    logger.warning(f"Petitioner not found for gmail: {applicant.gmail}")

            # Delete related PendingUser (applicant) and the notification itself
            fresh_instance.delete()
            if applicant:
                applicant.delete()

            # Return the petitioner instance (or None if not found)
            return petitioner



            

    def move_to_archive(self):
        from pendingusers.models.ArchivedPendingUser import ArchivedPendingUser
        try:
            with transaction.atomic():
                fresh_instance = InitiationNotification.objects.select_for_update().get(pk=self.pk)
                logger.info(f"Moving notification {fresh_instance.id} to archive")
                
                archived_notification = ArchivedPendingUser(
                    gmail=fresh_instance.applicant.gmail,
                    initiator_id=fresh_instance.initiator.id,
                    status=fresh_instance.status,
                    archived_at=now()
                )
                archived_notification.save()
                
                # Delete related objects first
                applicant = fresh_instance.applicant
                fresh_instance.delete()
                applicant.delete()
                
        except Exception as e:
            logger.error(f"Archive error: {str(e)}")
            raise

    @staticmethod
    def sanitize_email(email):
        return re.sub(r'[^a-zA-Z0-9]', '_', email)