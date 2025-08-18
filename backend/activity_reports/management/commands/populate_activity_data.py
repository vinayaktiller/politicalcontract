from django.core.management.base import BaseCommand
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
        
        # Create a mapping of user IDs to their join dates
        user_join_dates = dict(
            Petitioner.objects.values_list('id', 'date_joined__date')
        )
        
        current_date = start_date
        days_processed = 0
        
        while current_date <= end_date:
            # Eligible users: joined on or before today
            eligible_users = [
                user_id for user_id in all_users 
                if user_join_dates[user_id] <= current_date
            ]
            
            if not eligible_users:
                current_date += timedelta(days=1)
                continue
                
            # Determine number of active users today
            raw_count = max(min_active, int(len(eligible_users) * probability))
            active_count = min(raw_count, max_active, len(eligible_users))  # <-- FIX: cap at population size
            
            # Select active users randomly
            active_users = random.sample(eligible_users, active_count)
            
            # Create daily summary
            DailyActivitySummary.objects.update_or_create(
                date=current_date,
                defaults={'active_users': active_users}
            )
            
            # Track monthly updates per user
            monthly_updates = defaultdict(list)
            for user_id in active_users:
                day_of_month = current_date.day
                month_key = (user_id, current_date.year, current_date.month)
                if day_of_month not in monthly_updates[month_key]:
                    monthly_updates[month_key].append(day_of_month)
            
            # Save or update UserMonthlyActivity
            for (user_id, year, month), days in monthly_updates.items():
                try:
                    record = UserMonthlyActivity.objects.get(
                        user_id=user_id, year=year, month=month
                    )
                    existing_days = set(record.active_days)
                    existing_days.update(days)
                    record.active_days = sorted(existing_days)
                    record.save()
                except UserMonthlyActivity.DoesNotExist:
                    UserMonthlyActivity.objects.create(
                        user_id=user_id,
                        year=year,
                        month=month,
                        active_days=days
                    )
            
            # Progress counter
            current_date += timedelta(days=1)
            days_processed += 1
            
            if days_processed % 10 == 0:
                self.stdout.write(
                    f"Processed {days_processed} days... "
                    f"(last day: {current_date - timedelta(days=1)}, active users: {active_count})"
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully populated {days_processed} days of activity data'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Created/updated {UserMonthlyActivity.objects.count()} monthly activity records'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Created/updated {DailyActivitySummary.objects.count()} daily summary records'
        ))
