from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Sets up hyperactive scenario for testing'

    def handle(self, *args, **kwargs):
        user_id = '11021801300001'
        today = date.today()

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

        # Define 5-day streak ending today
        streak_dates = [today - timedelta(days=i) for i in range(4, -1, -1)]
        streak_days = sorted(set(date.day for date in streak_dates))

        # Append missing days
        for day in streak_days:
            if day not in activity.active_days:
                activity.active_days.append(day)

        activity.active_days = sorted(set(activity.active_days))
        activity.save()

        self.stdout.write(self.style.SUCCESS(
            f'Hyperactive scenario set for user {user_id}:\n'
            f'→ Streak: {streak_days[0]} to {streak_days[-1]} {today.strftime("%B")}'
        ))
