# management/commands/delete_user.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from users.models import UserTree, Petitioner, Milestone, Circle
from chat.models import Conversation, Message
from activity_reports.models import UserMonthlyActivity, DailyActivitySummary
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Completely delete a user and all related instances across all models'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='ID of the user to delete')

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        try:
            with transaction.atomic():
                self.stdout.write(f"Starting deletion process for user ID: {user_id}")
                
                # 1. Delete messages where user is sender or receiver
                Message.objects.filter(
                    Q(sender_id=user_id) | Q(receiver_id=user_id)
                ).delete()
                self.stdout.write("Deleted messages")
                
                # 2. Delete conversations where user is participant
                Conversation.objects.filter(
                    Q(participant1_id=user_id) | Q(participant2_id=user_id)
                ).delete()
                self.stdout.write("Deleted conversations")
                
                # 3. Delete circle relationships where user is involved
                Circle.objects.filter(
                    Q(userid=user_id) | Q(otherperson=user_id)
                ).delete()
                self.stdout.write("Deleted circle relationships")
                
                # 4. Delete milestones
                Milestone.objects.filter(user_id=user_id).delete()
                self.stdout.write("Deleted milestones")
                
                # 5. Delete activity records
                UserMonthlyActivity.objects.filter(user_id=user_id).delete()
                self.stdout.write("Deleted monthly activity records")
                
                # 6. Remove user from daily activity summaries
                daily_summaries = DailyActivitySummary.objects.filter(active_users__contains=[user_id])
                for summary in daily_summaries:
                    summary.active_users.remove(user_id)
                    summary.save()
                self.stdout.write("Removed user from daily activity summaries")
                
                # 7. Handle UserTree relationships
                user_tree = UserTree.objects.filter(id=user_id).first()
                if user_tree:
                    # Reassign children to parent if exists
                    children = UserTree.objects.filter(parentid=user_id)
                    for child in children:
                        child.parentid = user_tree.parentid
                        child.save()
                    
                    # Update parent's childcount if exists
                    if user_tree.parentid:
                        parent = user_tree.parentid
                        parent.childcount = max(0, parent.childcount - 1)
                        parent.save()
                    
                    user_tree.delete()
                    self.stdout.write("Deleted UserTree record and updated relationships")
                
                # 8. Finally delete the petitioner
                Petitioner.objects.filter(id=user_id).delete()
                self.stdout.write("Deleted petitioner record")
                
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully deleted user {user_id} and all related data")
                )
                
        except Exception as e:
            raise CommandError(f"Error deleting user {user_id}: {str(e)}")