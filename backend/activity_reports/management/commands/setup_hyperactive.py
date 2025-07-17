from django.core.management.base import BaseCommand
from activity_reports.models import UserMonthlyActivity
from users.models import Petitioner
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Sets up hyperactive scenario for testing'
    
    def handle(self, *args, **kwargs):
        user_id = '11021801300001'
        today = date(2025, 7, 12)
        
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
        
        # Create 5-day streak (8th to 12th)
        streak_days = [today - timedelta(days=i) for i in range(5)]
        new_days = [d.day for d in streak_days]
        
        # Add streak days if not already present
        for day in new_days:
            if day not in activity.active_days:
                activity.active_days.append(day)
                
        activity.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Hyperactive scenario set for user {user_id}: '
            f'5-day streak from {min(new_days)} to {max(new_days)} July'
        ))
        