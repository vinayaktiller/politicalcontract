from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Sets up active scenario for testing'

    def handle(self, *args, **kwargs):
        user_id = '11021801300001'
        today = date.today()
        yesterday = today - timedelta(days=1)

        try:
            user = Petitioner.objects.get(id=user_id)
        except Petitioner.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {user_id} not found'))
            return

        activity, created = UserMonthlyActivity.objects.get_or_create(
            user=user,
            year=today.year,
            month=today.month,
            defaults={'active_days': []}
        )

        # Ensure yesterday and today are marked active
        active_day_nums = [yesterday.day, today.day]
        for day_num in active_day_nums:
            if day_num not in activity.active_days:
                activity.active_days.append(day_num)

        activity.save()

        self.stdout.write(self.style.SUCCESS(
            f'Active scenario set for user {user_id}:\n'
            f'→ Yesterday: {yesterday.strftime("%Y-%m-%d")}\n'
            f'→ Today: {today.strftime("%Y-%m-%d")}'
        ))
