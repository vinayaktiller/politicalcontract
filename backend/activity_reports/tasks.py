from celery import shared_task
from django.utils import timezone
from datetime import datetime
import random
from users.models import Petitioner
from activity_reports.models import UserMonthlyActivity, DailyActivitySummary
from django.db import transaction
from django.db import IntegrityError
import logging
from activity_reports.signals import send_activity_update  # Import the signal handler

logger = logging.getLogger(__name__)

@shared_task
def simulate_realtime_activity():
    # Configuration parameters
    DAILY_PROBABILITY = 0.4
    MAX_INTERVAL_ACTIVE = 100
    MIN_INTERVAL_ACTIVE = 1
    
    now = timezone.now()
    today = now.date()
    day_of_month = today.day
    year, month = today.year, today.month
    
    # Calculate interval probability (3 minutes out of 1440 daily minutes)
    interval_probability = DAILY_PROBABILITY * (3 / 1440)
    
    # Get all users who joined before now
    eligible_users = list(Petitioner.objects.filter(
        date_joined__lt=now
    ).values_list('id', flat=True))
    
    if not eligible_users:
        return "No eligible users found."
    
    # Calculate active users for this interval
    active_count = max(
        MIN_INTERVAL_ACTIVE,
        min(MAX_INTERVAL_ACTIVE, int(len(eligible_users) * interval_probability))
    )
    active_users = random.sample(eligible_users, active_count)
    
    summary = None
    
    # 1. Update daily activity summary with proper locking
    try:
        with transaction.atomic():
            # Lock the daily summary record for update
            summary, created = DailyActivitySummary.objects.select_for_update().get_or_create(
                date=today,
                defaults={'active_users': active_users}
            )
            
            if not created:
                # Merge and deduplicate user IDs in Python
                existing_users = set(summary.active_users)
                new_users = set(active_users)
                updated_users = list(existing_users | new_users)
                
                summary.active_users = updated_users
                summary.save()
    except IntegrityError:
        # Handle race condition by refetching with lock
        with transaction.atomic():
            summary = DailyActivitySummary.objects.select_for_update().get(date=today)
            existing_users = set(summary.active_users)
            new_users = set(active_users)
            updated_users = list(existing_users | new_users)
            
            summary.active_users = updated_users
            summary.save()
    
    # MANUALLY TRIGGER SIGNAL AFTER SAVING DAILY SUMMARY
    if summary:
        try:
            logger.info(f"[Task] Manually triggering signal for {summary.date}")
            send_activity_update(DailyActivitySummary, summary)
        except Exception as e:
            logger.error(f"[Task Error] Signal trigger failed: {e}")
    
    # 2. Update monthly activity records
    # Create a list of records to update
    records_to_update = []
    
    # FIX: Replace in_bulk() with manual dictionary creation
    monthly_records = {}
    for record in UserMonthlyActivity.objects.filter(
        user_id__in=active_users,
        year=year,
        month=month
    ):
        # Handle potential duplicates (shouldn't occur due to unique constraint)
        if record.user_id in monthly_records:
            # Merge active days if duplicate found (unlikely but safe)
            monthly_records[record.user_id].active_days = list(
                set(monthly_records[record.user_id].active_days + record.active_days)
            )
        else:
            monthly_records[record.user_id] = record
    
    for user_id in active_users:
        record = monthly_records.get(user_id)
        
        if record:
            # Check if day needs to be added
            if day_of_month not in record.active_days:
                record.active_days.append(day_of_month)
                records_to_update.append(record)
        else:
            # Create new record
            records_to_update.append(UserMonthlyActivity(
                user_id=user_id,
                year=year,
                month=month,
                active_days=[day_of_month]
            ))
    
    # Update records in bulk with locking
    for record in records_to_update:
        with transaction.atomic():
            if record.pk:  # Existing record
                # Reload with lock to prevent race conditions
                locked_record = UserMonthlyActivity.objects.select_for_update().get(pk=record.pk)
                # Ensure day hasn't been added by another process
                if day_of_month not in locked_record.active_days:
                    locked_record.active_days.append(day_of_month)
                    locked_record.save()
            else:  # New record
                try:
                    record.save()
                except IntegrityError:
                    # Handle race condition if record was created by another process
                    existing = UserMonthlyActivity.objects.get(
                        user_id=record.user_id,
                        year=record.year,
                        month=record.month
                    )
                    if day_of_month not in existing.active_days:
                        existing.active_days.append(day_of_month)
                        existing.save()
    
    return f"Updated {len(active_users)} users at {now.strftime('%Y-%m-%d %H:%M:%S')}"

# we will remove the above part only below part will be there in production.

from celery import shared_task
from django.utils import timezone
from datetime import datetime
import random
from users.models import Petitioner
from activity_reports.models import UserMonthlyActivity, DailyActivitySummary
from django.db import transaction
from django.db import IntegrityError
import logging
from activity_reports.signals import send_activity_update  # Import the signal handler

logger = logging.getLogger(__name__)

@shared_task
def simulate_realtime_activity():
    # Configuration parameters
    DAILY_PROBABILITY = 0.4
    MAX_INTERVAL_ACTIVE = 100
    MIN_INTERVAL_ACTIVE = 1
    
    now = timezone.now()
    today = now.date()
    day_of_month = today.day
    year, month = today.year, today.month
    
    # Calculate interval probability (3 minutes out of 1440 daily minutes)
    interval_probability = DAILY_PROBABILITY * (3 / 1440)
    
    # Get all users who joined before now
    eligible_users = list(Petitioner.objects.filter(
        date_joined__lt=now
    ).values_list('id', flat=True))
    
    if not eligible_users:
        return "No eligible users found."
    
    # Calculate active users for this interval
    active_count = max(
        MIN_INTERVAL_ACTIVE,
        min(MAX_INTERVAL_ACTIVE, int(len(eligible_users) * interval_probability))
    )
    active_users = random.sample(eligible_users, active_count)
    
    summary = None
    
    # 1. Update daily activity summary with proper locking
    try:
        with transaction.atomic():
            # Lock the daily summary record for update
            summary, created = DailyActivitySummary.objects.select_for_update().get_or_create(
                date=today,
                defaults={'active_users': active_users}
            )
            
            if not created:
                # Merge and deduplicate user IDs in Python
                existing_users = set(summary.active_users)
                new_users = set(active_users)
                updated_users = list(existing_users | new_users)
                
                summary.active_users = updated_users
                summary.save()
    except IntegrityError:
        # Handle race condition by refetching with lock
        with transaction.atomic():
            summary = DailyActivitySummary.objects.select_for_update().get(date=today)
            existing_users = set(summary.active_users)
            new_users = set(active_users)
            updated_users = list(existing_users | new_users)
            
            summary.active_users = updated_users
            summary.save()
    
    # MANUALLY TRIGGER SIGNAL AFTER SAVING DAILY SUMMARY
    if summary:
        try:
            logger.info(f"[Task] Manually triggering signal for {summary.date}")
            send_activity_update(DailyActivitySummary, summary)
        except Exception as e:
            logger.error(f"[Task Error] Signal trigger failed: {e}")
    
    # 2. Update monthly activity records
    # Create a list of records to update
    records_to_update = []
    
    # FIX: Replace in_bulk() with manual dictionary creation
    monthly_records = {}
    for record in UserMonthlyActivity.objects.filter(
        user_id__in=active_users,
        year=year,
        month=month
    ):
        # Handle potential duplicates (shouldn't occur due to unique constraint)
        if record.user_id in monthly_records:
            # Merge active days if duplicate found (unlikely but safe)
            monthly_records[record.user_id].active_days = list(
                set(monthly_records[record.user_id].active_days + record.active_days)
            )
        else:
            monthly_records[record.user_id] = record
    
    for user_id in active_users:
        record = monthly_records.get(user_id)
        
        if record:
            # Check if day needs to be added
            if day_of_month not in record.active_days:
                record.active_days.append(day_of_month)
                records_to_update.append(record)
        else:
            # Create new record
            records_to_update.append(UserMonthlyActivity(
                user_id=user_id,
                year=year,
                month=month,
                active_days=[day_of_month]
            ))
    
    # Update records in bulk with locking
    for record in records_to_update:
        with transaction.atomic():
            if record.pk:  # Existing record
                # Reload with lock to prevent race conditions
                locked_record = UserMonthlyActivity.objects.select_for_update().get(pk=record.pk)
                # Ensure day hasn't been added by another process
                if day_of_month not in locked_record.active_days:
                    locked_record.active_days.append(day_of_month)
                    locked_record.save()
            else:  # New record
                try:
                    record.save()
                except IntegrityError:
                    # Handle race condition if record was created by another process
                    existing = UserMonthlyActivity.objects.get(
                        user_id=record.user_id,
                        year=record.year,
                        month=record.month
                    )
                    if day_of_month not in existing.active_days:
                        existing.active_days.append(day_of_month)
                        existing.save()
    
    return f"Updated {len(active_users)} users at {now.strftime('%Y-%m-%d %H:%M:%S')}"