from django.core.management.base import BaseCommand
from users.models import Milestone

class Command(BaseCommand):
    help = 'Delete all milestones for the user ID 11021801300001.'

    def handle(self, *args, **kwargs):
        user_id = 11021801300001
        milestones = Milestone.objects.filter(user_id=user_id)
        count = milestones.count()
        milestones.delete()
        self.stdout.write(self.style.SUCCESS(
            f'Successfully deleted {count} milestones for user_id {user_id}.'
        ))
