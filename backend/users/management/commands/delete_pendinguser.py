from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pendingusers.models import PendingUser, InitiationNotification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Delete a PendingUser and all related InitiationNotifications by Gmail'

    def add_arguments(self, parser):
        parser.add_argument('gmail', type=str, help='Gmail of the PendingUser to delete')

    def handle(self, *args, **options):
        gmail = options['gmail']
        try:
            with transaction.atomic():
                self.stdout.write(f"Starting deletion process for PendingUser gmail: {gmail}")

                # Find PendingUser
                pending_user = PendingUser.objects.filter(gmail=gmail).first()
                if not pending_user:
                    self.stdout.write(
                        self.style.WARNING(f"PendingUser with gmail {gmail} does not exist.")
                    )
                    return

                # Delete InitiationNotifications related to this PendingUser
                notifications_deleted, _ = InitiationNotification.objects.filter(applicant=pending_user).delete()
                self.stdout.write(f"Deleted {notifications_deleted} related InitiationNotification(s)")

                # Delete the PendingUser
                pending_user.delete()
                self.stdout.write("Deleted PendingUser record")

                self.stdout.write(
                    self.style.SUCCESS(f"Successfully deleted PendingUser {gmail} and related notifications.")
                )
        except Exception as e:
            logger.error(f"Error deleting PendingUser {gmail}: {str(e)}")
            raise CommandError(f"Error deleting PendingUser {gmail}: {str(e)}")
