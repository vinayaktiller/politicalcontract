# management/commands/populate_activity_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from users.models import Petitioner
from activity_reports.models import UserMonthlyActivity, DailyActivitySummary
import random
from collections import defaultdict

class Command(BaseCommand):
    help = 'Populates activity data with realistic random user activity patterns'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--probability',
            type=float,
            default=0.4,
            help='Probability of a user being active on any given day (default: 0.4)'
        )
        parser.add_argument(
            '--max-active',
            type=int,
            default=1000,
            help='Maximum number of active users per day (default: 1000)'
        )
        parser.add_argument(
            '--min-active',
            type=int,
            default=10,
            help='Minimum number of active users per day (default: 10)'
        )
    
    def handle(self, *args, **kwargs):
        probability = kwargs['probability']
        max_active = kwargs['max_active']
        min_active = kwargs['min_active']
        
        # Get date range
        first_user = Petitioner.objects.order_by('date_joined').first()
        if not first_user:
            self.stdout.write(self.style.ERROR('No users found in the database'))
            return
            
        start_date = first_user.date_joined.date()
        end_date = date.today()
        
        self.stdout.write(self.style.SUCCESS(
            f'Generating activity data from {start_date} to {end_date}'
        ))
        
        # Pre-fetch all users once
        all_users = list(Petitioner.objects.all().values_list('id', flat=True))
        if not all_users:
            self.stdout.write(self.style.ERROR('No users found in the database'))
            return
            
        self.stdout.write(f"Found {len(all_users)} users in the database")
        
        # Track active users per day
        daily_activity = {}
        
        # Create a mapping of user IDs to their join dates
        user_join_dates = dict(
            Petitioner.objects.values_list('id', 'date_joined__date')
        )
        
        # For each day in our range
        current_date = start_date
        days_processed = 0
        
        while current_date <= end_date:
            # Users who could be active today (joined before today)
            eligible_users = [
                user_id for user_id in all_users 
                if user_join_dates[user_id] <= current_date
            ]
            
            if not eligible_users:
                current_date += timedelta(days=1)
                continue
                
            # Determine how many users will be active today
            active_count = min(
                max(min_active, int(len(eligible_users) * probability)),
                max_active
            )
            
            # Randomly select active users
            active_users = random.sample(eligible_users, active_count)
            daily_activity[current_date] = active_users
            
            # Create daily summary
            DailyActivitySummary.objects.update_or_create(
                date=current_date,
                defaults={'active_users': active_users}
            )
            
            # Prepare monthly activity updates
            monthly_updates = defaultdict(list)
            for user_id in active_users:
                # Get day of month (1-31)
                day_of_month = current_date.day
                
                # Create key for monthly tracking
                month_key = (user_id, current_date.year, current_date.month)
                
                # Add day to this month's activity
                if day_of_month not in monthly_updates[month_key]:
                    monthly_updates[month_key].append(day_of_month)
            
            # Update monthly activity records
            for (user_id, year, month), days in monthly_updates.items():
                # Get existing record
                try:
                    record = UserMonthlyActivity.objects.get(
                        user_id=user_id,
                        year=year,
                        month=month
                    )
                    # Merge and deduplicate days
                    existing_days = set(record.active_days)
                    existing_days.update(days)
                    record.active_days = sorted(existing_days)
                    record.save()
                except UserMonthlyActivity.DoesNotExist:
                    # Create new record
                    UserMonthlyActivity.objects.create(
                        user_id=user_id,
                        year=year,
                        month=month,
                        active_days=days
                    )
            
            # Progress tracking
            current_date += timedelta(days=1)
            days_processed += 1
            
            if days_processed % 10 == 0:
                self.stdout.write(f"Processed {days_processed} days...")
                self.stdout.write(f"  Today: {current_date - timedelta(days=1)} - {active_count} active users")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully populated {days_processed} days of activity data'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Created {UserMonthlyActivity.objects.count()} monthly activity records'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Created {DailyActivitySummary.objects.count()} daily summary records'
        ))