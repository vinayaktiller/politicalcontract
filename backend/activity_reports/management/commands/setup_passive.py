from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Sets up passive scenario for testing'
    
    def handle(self, *args, **kwargs):
        user_id = '11021801300001'
        today = date.today()
        yesterday = today - timedelta(days=1)

        try:
            user = Petitioner.objects.get(id=user_id)
        except Petitioner.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {user_id} not found'))
            return

        # Get or create the monthly activity record
        activity, created = UserMonthlyActivity.objects.get_or_create(
            user=user,
            year=today.year,
            month=today.month,
            defaults={'active_days': []}
        )

        # Make sure active_days is initialized
        if activity.active_days is None:
            activity.active_days = []

        # Ensure yesterday is active
        if yesterday.day not in activity.active_days:
            activity.active_days.append(yesterday.day)
            self.stdout.write(f'✔️ Marked {yesterday.day} as active')

        # Ensure today is inactive
        if today.day in activity.active_days:
            activity.active_days.remove(today.day)
            self.stdout.write(f'🚫 Marked {today.day} as inactive')

        activity.save(update_fields=['active_days'])

        self.stdout.write(self.style.SUCCESS(
            f'Passive scenario set for user {user_id}: '
            f'Active yesterday ({yesterday.day}), inactive today ({today.day})'
        ))
