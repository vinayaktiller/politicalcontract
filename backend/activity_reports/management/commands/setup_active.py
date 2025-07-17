from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date

class Command(BaseCommand):
    help = 'Sets up active scenario for testing'
    
    def handle(self, *args, **kwargs):
        user_id = '11021801300001'
        today = date(2025, 7, 12)
        yesterday_day = today.day - 1
        
        try:
            user = Petitioner.objects.get(id=user_id)
        except Petitioner.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {user_id} not found'))
            return
            
        # Get or create monthly activity record
        activity, created = UserMonthlyActivity.objects.get_or_create(
            user=user,
            year=today.year,
            month=today.month,
            defaults={'active_days': []}
        )
        
        # Ensure both days are active
        for day in [yesterday_day, today.day]:
            if day not in activity.active_days:
                activity.active_days.append(day)
                
        activity.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Active scenario set for user {user_id}: '
            f'Active both yesterday ({yesterday_day}) and today ({today.day})'
        ))