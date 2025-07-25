from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Sets up inactive scenario for testing'

    def handle(self, *args, **kwargs):
        user_id = '11021801300001'
        today = date.today()
        yesterday = today - timedelta(days=1)

        try:
            user = Petitioner.objects.get(id=user_id)
        except Petitioner.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ User {user_id} not found'))
            return

        activity, created = UserMonthlyActivity.objects.get_or_create(
            user=user,
            year=today.year,
            month=today.month,
            defaults={'active_days': []}
        )

        # Ensure active_days is initialized
        if activity.active_days is None:
            activity.active_days = []

        # Remove today and yesterday from active_days
        filtered_days = [
            d for d in activity.active_days
            if d not in [today.day, yesterday.day]
        ]

        activity.active_days = filtered_days
        activity.save(update_fields=['active_days'])

        self.stdout.write(self.style.SUCCESS(
            f'🛑 Inactive scenario set for user {user_id}: '
            f'No activity on {yesterday.day} or {today.day}'
        ))
