from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date

class Command(BaseCommand):
    help = 'Sets up inactive scenario for testing'
    
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
        
        # Remove today and yesterday from active days
        updated_days = [
            d for d in activity.active_days 
            if d not in [today.day, yesterday_day]
        ]
        activity.active_days = updated_days
        activity.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Inactive scenario set for user {user_id}: '
            f'No activity on {yesterday_day} or {today.day}'
        ))