from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from users.models import Petitioner
from users.models import AdditionalInfo
import random
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create AdditionalInfo instances for users who dont have it yet with random geographical data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to process in each batch (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.NOTICE(
                f"Finding users without AdditionalInfo (dry-run: {dry_run})..."
            )
        )

        # Get users who don't have AdditionalInfo
        users_without_info = Petitioner.objects.exclude(
            id__in=AdditionalInfo.objects.values_list('user_id', flat=True)
        )
        total_users_needed = users_without_info.count()

        self.stdout.write(
            self.style.NOTICE(f"Found {total_users_needed} users without AdditionalInfo")
        )

        if total_users_needed == 0:
            self.stdout.write(
                self.style.SUCCESS("All users already have AdditionalInfo! Nothing to do.")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No records will be created")
            )

        created_count = 0
        error_count = 0

        # Process users in batches
        for i in range(0, total_users_needed, batch_size):
            batch_users = users_without_info[i:i + batch_size]
            
            self.stdout.write(
                f"Processing batch {i//batch_size + 1}/{(total_users_needed + batch_size - 1)//batch_size} "
                f"(users {i+1} to {min(i+batch_size, total_users_needed)})"
            )

            for user in batch_users:
                try:
                    if not dry_run:
                        # Create AdditionalInfo with random geographical data
                        additional_info = AdditionalInfo.objects.create(
                            user_id=user.id,
                            village_number=random.randint(1, 50),
                            subdistrict_number=random.randint(1, 20),
                            district_number=random.randint(1, 10),
                            state_number=random.randint(1, 5),
                            country_number=1,  # Assuming all users are from the same country
                            active_days=0,
                            last_active_date=None
                        )
                        created_count += 1
                        
                        if created_count % 50 == 0:
                            self.stdout.write(
                                self.style.SUCCESS(f"Created {created_count} AdditionalInfo records so far...")
                            )
                    else:
                        created_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"Error creating AdditionalInfo for user {user.id}: {str(e)}")
                    )
                    logger.error(f"Error creating AdditionalInfo for user {user.id}: {str(e)}")

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("PROCESSING COMPLETE"))
        self.stdout.write("="*50)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN - Would have created: {created_count} records")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created: {created_count} AdditionalInfo records")
            )
            
        self.stdout.write(
            self.style.ERROR(f"Errors encountered: {error_count} users")
        )
        
        if not dry_run:
            # Verify the results
            total_with_additional_info = AdditionalInfo.objects.count()
            remaining_without_info = Petitioner.objects.exclude(
                id__in=AdditionalInfo.objects.values_list('user_id', flat=True)
            ).count()
            
            self.stdout.write(
                self.style.NOTICE(f"Total AdditionalInfo records in database: {total_with_additional_info}")
            )
            
            if remaining_without_info > 0:
                self.stdout.write(
                    self.style.WARNING(f"Users still without AdditionalInfo: {remaining_without_info}")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("All users now have AdditionalInfo records!")
                )