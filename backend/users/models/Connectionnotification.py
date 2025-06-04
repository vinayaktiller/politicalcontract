from django.db import models, transaction
from django.utils.timezone import now
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import re
import logging
import threading
from users.models.petitioners import Petitioner
import traceback

logger = logging.getLogger(__name__)

class ConnectionNotification(models.Model):
    class Status(models.TextChoices):
        CONNECTION_OFFLINE = "connection_offline", "Connection Offline"
        SENT = "sent", "Sent"
        NOT_VIEWED = "not_viewed", "Not Viewed"
        REACTED_PENDING = "reacted_pending", "Reacted Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    STATUS_MESSAGES = {
        Status.CONNECTION_OFFLINE: "⚠️ The request recipient is currently offline...",
        Status.SENT: "✅ Your connection request has been sent...",
        Status.NOT_VIEWED: "👀 Your connection request has been sent...",
        Status.REACTED_PENDING: "⏳ The recipient has seen your request...",
        Status.ACCEPTED: "🎉 Your request has been accepted!",
        Status.REJECTED: "🚫 Your request has been rejected."
    }

    connection = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name="sent_connexion_notifications")
    applicant = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name="received_connexion_notifications")
    status = models.CharField(max_length=20, choices=Status.choices, default=None, null=True, blank=True)
    sent = models.BooleanField(default=False)
    viewed = models.BooleanField(default=False)
    reacted = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'userschema"."connectionnotification'
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["applicant", "status"]),
        ]

    def __str__(self):
        return f"ConnectionNotification from {self.connection} to {self.applicant} - Status: {self.status}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            if self.connection.is_online:
                self.process_notification()
                from ..makingconnections.services.send_status_to_applicant import send_status_to_applicant
                send_status_to_applicant(self)
                
            else:
                self._set_offline_status()

    def process_notification(self):
        from ..makingconnections.services.send_notfication_to_connection import send_notification_to_connection

        send_notification_to_connection(self)
        self.sent = True
        self.status = self.Status.SENT
        self.save(update_fields=["sent", "status"])
        self.mark_as_not_viewed()

    def update_status(self, new_status):
        if self.status == new_status:
            return
        self.status = new_status
        self.save(update_fields=["status"])
        logger.info(f"send data to applicant {self.applicant.id} for connection {self.id}")
        from ..makingconnections.services.send_status_to_applicant import send_status_to_applicant
        send_status_to_applicant(self)
        
        logger.info(f"ConnectionNotification {self.id} status updated to {new_status}")

    # def send_websocket_notification(self):
    #     try:
    #         channel_layer = get_channel_layer()
    #         sanitized_email = self.sanitize_email(self.applicant.gmail)
    #         group_name = f"connexions_{sanitized_email}"
    #         message = self.STATUS_MESSAGES.get(self.status, "Unknown status update.")

    #         async_to_sync(channel_layer.group_send)(
    #             group_name,
    #             {
    #                 "type": "connexions_message",
    #                 "notification_id": self.id,
    #                 "status": self.status,
    #                 "message": message
    #             }
    #         )
    #     except Exception as e:
    #         logger.error(f"WebSocket notification failed: {str(e)}")

    def _set_offline_status(self):
        try:
            self.refresh_from_db()
            if not self.sent:
                self.update_status(self.Status.CONNECTION_OFFLINE)
        except ConnectionNotification.DoesNotExist:
            logger.warning("Notification deleted before offline status could be set")

    def mark_as_not_viewed(self):
        threading.Timer(30, self._safely_set_not_viewed_status).start()

    def _safely_set_not_viewed_status(self):
        try:
            with transaction.atomic():
                fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
                if not fresh_instance.viewed:
                    fresh_instance.update_status(self.Status.NOT_VIEWED)
        except ConnectionNotification.DoesNotExist:
            logger.info("Notification deleted before not-viewed status could be set")

    def mark_as_viewed(self):
        try:
            with transaction.atomic():
                fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
                fresh_instance.viewed = True
                fresh_instance.save(update_fields=["viewed"])
                fresh_instance.mark_as_reacted_pending()
        except ConnectionNotification.DoesNotExist:
            logger.warning("Notification deleted before viewed status could be set")

    def mark_as_reacted_pending(self):
        threading.Timer(30, self._safely_set_reacted_pending_status).start()

    def _safely_set_reacted_pending_status(self):
        try:
            with transaction.atomic():
                fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
                if not fresh_instance.reacted:
                    fresh_instance.update_status(self.Status.REACTED_PENDING)
        except ConnectionNotification.DoesNotExist:
            logger.info("Notification deleted before reacted-pending status could be set")

    def mark_as_accepted(self):
        from ..makingconnections.makingcircleinstances.create_connection_circles import create_connection_circles
        with transaction.atomic():
            try:
                fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
                fresh_instance.reacted = True
                fresh_instance.save(update_fields=["reacted"])
                fresh_instance.update_status(self.Status.ACCEPTED)

                # Attempt to create connection circles
                create_connection_circles(fresh_instance)

            except ConnectionNotification.DoesNotExist:
                print(f"Error: ConnectionNotification with ID {self.pk} not found.")
            except Exception as e:
                print(f"Unexpected error while marking as accepted: {e}")


    def mark_as_rejected(self):
        with transaction.atomic():
            fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
            fresh_instance.reacted = True
            fresh_instance.save(update_fields=["reacted"])
            fresh_instance.update_status(self.Status.REJECTED)
            

    def mark_as_completed(self):
        with transaction.atomic():
            try:
                fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
                fresh_instance.completed = True
                fresh_instance.save(update_fields=["completed"])
                
                # Delete the notification instance after marking it as completed
                fresh_instance.delete()
                
                print(f"ConnectionNotification with ID {self.pk} has been marked as completed and deleted.")

            except ConnectionNotification.DoesNotExist:
                print(f"Error: ConnectionNotification with ID {self.pk} not found.")
            except Exception as e:
                print(f"Unexpected error while completing and deleting notification: {e}")
    def mark_as_dropped(self):
        with transaction.atomic():
            try:
                fresh_instance = ConnectionNotification.objects.select_for_update().get(pk=self.pk)
                fresh_instance.completed = True
                fresh_instance.save(update_fields=["completed"])
                from ..makingconnections.services.delete_notification_from_connection import delete_notification_from_connection
                delete_notification_from_connection(self)
                # Delete the notification instance after marking it as completed
                
                
                print(f"ConnectionNotification with ID {self.pk} has been marked as dropped and deleted.")

            except ConnectionNotification.DoesNotExist:
                print(f"Error: ConnectionNotification with ID {self.pk} not found.")
            except Exception as e:
                print(f"Unexpected error while dropping and deleting notification: {e}")

            


    # @staticmethod
    # def sanitize_email(email):
    #     return re.sub(r'[^a-zA-Z0-9]', '_', email)