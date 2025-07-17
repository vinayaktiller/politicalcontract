from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Max
from datetime import date, timedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import CumulativeReport
from users.models import Petitioner
from collections import defaultdict

class Command(BaseCommand):
    help = 'Updates cumulative reports incrementally with test data cleanup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: last processed date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: yesterday)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing reports before processing the date range'
        )

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        
        if kwargs['clean']:
            self.stdout.write("Cleaning existing reports...")
            self.clean_reports(start_date, end_date)
        
        self.stdout.write(f"Updating cumulative reports from {start_date} to {end_date}")
        current_date = start_date
        processed_days = 0
        
        while current_date <= end_date:
            self.stdout.write(f"Processing {current_date}...")
            
            with transaction.atomic():
                # First clean any existing data for this specific date
                self.clean_date(current_date)
                # Then process new data for the date
                self.process_daily_users(current_date)
            
            current_date += timedelta(days=1)
            processed_days += 1
            
            if processed_days % 7 == 0:
                self.stdout.write(f"Processed {processed_days} days...")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully updated cumulative reports for {processed_days} days'
        ))

    def get_date_range(self, kwargs):
        # Find last processed date from cumulative reports
        last_processed = CumulativeReport.objects.aggregate(
            max_date=Max('last_updated__date')
        )['max_date']
        
        # Default start is day after last processed or first user date
        if last_processed:
            default_start = last_processed + timedelta(days=1)
        else:
            first_user = Petitioner.objects.order_by('date_joined').first()
            if not first_user:
                self.stdout.write(self.style.WARNING('No users found. Exiting.'))
                exit(0)
            default_start = first_user.date_joined.date()
        
        # Default end is yesterday
        default_end = date.today() - timedelta(days=1)
        
        start_date = (
            date.fromisoformat(kwargs['start_date'])
            if kwargs.get('start_date')
            else default_start
        )
        end_date = (
            date.fromisoformat(kwargs['end_date'])
            if kwargs.get('end_date')
            else default_end
        )
        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date > date.today():
            raise ValueError("End date cannot be in the future")
        
        return start_date, end_date

    def clean_reports(self, start_date, end_date):
        """Delete reports within date range for all geographic levels"""
        # Get user IDs created in the date range
        user_ids = Petitioner.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).values_list('id', flat=True)
        
        # Clean village reports (remove specific users from JSON)
        village_reports = CumulativeReport.objects.filter(level='village')
        for report in village_reports:
            if report.user_data:
                # Remove users created in our date range
                for uid in user_ids:
                    if str(uid) in report.user_data:
                        del report.user_data[str(uid)]
                        report.total_users -= 1
                
                if report.total_users < 0:
                    report.total_users = 0
                
                # Save if we modified or delete if empty
                if report.user_data:
                    report.save()
                else:
                    report.delete()
            else:
                report.delete()
        
        # Delete higher level reports completely
        CumulativeReport.objects.filter(level__in=[
            'subdistrict', 'district', 'state', 'country'
        ]).delete()

    def clean_date(self, process_date):
        """Remove existing data for a specific processing date"""
        # Get users created on this date
        user_ids = Petitioner.objects.filter(
            date_joined__date=process_date
        ).values_list('id', flat=True)
        
        # Clean village reports
        village_reports = CumulativeReport.objects.filter(level='village')
        for report in village_reports:
            if report.user_data:
                # Remove users created on this date
                for uid in user_ids:
                    if str(uid) in report.user_data:
                        del report.user_data[str(uid)]
                        report.total_users -= 1
                
                if report.total_users < 0:
                    report.total_users = 0
                
                # Save if we modified or delete if empty
                if report.user_data:
                    report.save()
                else:
                    report.delete()
            else:
                report.delete()
        
        # Higher levels will be recalculated during processing
        CumulativeReport.objects.filter(level__in=[
            'subdistrict', 'district', 'state', 'country'
        ]).delete()

    def process_daily_users(self, process_date):
        # Get new users for the day with geographic data
        new_users = Petitioner.objects.filter(
            date_joined__date=process_date
        ).exclude(
            village__isnull=True,
            subdistrict__isnull=True,
            district__isnull=True,
            state__isnull=True,
            country__isnull=True
        ).select_related('village', 'subdistrict', 'district', 'state', 'country')
        
        # Initialize aggregation dictionaries
        village_data = defaultdict(lambda: {'count': 0, 'user_data': {}})
        subdistrict_counts = defaultdict(int)
        district_counts = defaultdict(int)
        state_counts = defaultdict(int)
        country_counts = defaultdict(int)
        
        # Aggregate user data by geographic level
        for user in new_users:
            # Village level
            village_data[user.village.id]['count'] += 1
            village_data[user.village.id]['user_data'][str(user.id)] = f"{user.first_name} {user.last_name}"
            
            # Higher levels
            subdistrict_counts[user.subdistrict.id] += 1
            district_counts[user.district.id] += 1
            state_counts[user.state.id] += 1
            country_counts[user.country.id] += 1
        
        # Update cumulative reports
        self.update_village_reports(village_data)
        self.update_higher_level('subdistrict', subdistrict_counts)
        self.update_higher_level('district', district_counts)
        self.update_higher_level('state', state_counts)
        self.update_higher_level('country', country_counts)

    def update_village_reports(self, village_data):
        for village_id, data in village_data.items():
            # Get or create village cumulative report
            report, created = CumulativeReport.objects.get_or_create(
                level='village',
                geographical_entity=village_id,
                defaults={
                    'total_users': data['count'],
                    'user_data': data['user_data']
                }
            )
            
            if not created:
                # Update existing report
                current_data = report.user_data or {}
                current_data.update(data['user_data'])
                
                CumulativeReport.objects.filter(
                    level='village',
                    geographical_entity=village_id
                ).update(
                    total_users=F('total_users') + data['count'],
                    user_data=current_data
                )

    def update_higher_level(self, level, entity_counts):
        # Get existing reports for efficiency
        entity_ids = list(entity_counts.keys())
        existing_reports = CumulativeReport.objects.filter(
            level=level,
            geographical_entity__in=entity_ids
        )
        existing_map = {r.geographical_entity: r for r in existing_reports}
        
        # Prepare batch updates
        to_create = []
        to_update = []
        
        for entity_id, count in entity_counts.items():
            if entity_id in existing_map:
                to_update.append(entity_id)
            else:
                to_create.append(CumulativeReport(
                    level=level,
                    geographical_entity=entity_id,
                    total_users=count
                ))
        
        # Create new reports
        if to_create:
            CumulativeReport.objects.bulk_create(to_create)
        
        # Update existing reports
        if to_update:
            CumulativeReport.objects.filter(
                level=level,
                geographical_entity__in=to_update
            ).update(total_users=F('total_users') + count)