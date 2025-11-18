# reports/management/commands/generate_overall_reports.py

from django.core.management.base import BaseCommand
from django.db import transaction, models
from datetime import date, timedelta, datetime
import time
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import OverallReport
from users.models import Petitioner
from collections import defaultdict
from django.db.models import Prefetch
import pytz


class Command(BaseCommand):
    help = 'Generates cumulative overall reports for all geographic levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: last processed date or first user date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: yesterday)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing reports before processing'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed timing information'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk operations (default: 1000)'
        )

    def handle(self, *args, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        self.batch_size = kwargs.get('batch_size', 1000)
        
        # Get date range for processing
        start_date, end_date = self.get_date_range(kwargs)
        
        if kwargs['clean']:
            self.clean_existing_reports()
            self.stdout.write("🧹 Cleaned existing reports")

        self.stdout.write(f"📅 Generating cumulative reports from {start_date} to {end_date}")
        
        # Initialize minimal cache
        self.village_names = {}
        self.subdistrict_names = {}
        self.district_names = {}
        self.state_names = {}
        self.country_names = {}
        
        total_start_time = time.time()
        processed_days = self.process_date_range_incremental(start_date, end_date)
        
        # Update last_updated for all processed reports
        self.update_last_updated_timestamp()
        
        # Rebuild parent-child relationships and data
        self.rebuild_parent_data_with_all_children()
        
        total_time = time.time() - total_start_time
        
        self.stdout.write(self.style.SUCCESS(
            f'🎉 Successfully processed {processed_days} days in {total_time:.2f}s'
        ))

    def get_date_range(self, kwargs):
        """Get the date range for processing, checking country report's last_updated"""
        first_user = Petitioner.objects.order_by('date_joined').first()
        if not first_user:
            raise ValueError("No users found in database")
        
        default_start = first_user.date_joined.date()
        default_end = date.today() - timedelta(days=1)

        # Check country report to determine incremental start
        country_report = OverallReport.objects.filter(level='country').first()
        if country_report and not kwargs.get('start_date') and not kwargs.get('clean'):
            # Start from the day after the last update
            last_updated_date = country_report.last_updated.date()
            incremental_start = last_updated_date + timedelta(days=1)
            if incremental_start <= default_end:
                default_start = incremental_start
                self.stdout.write(f"🔄 Resuming from {default_start} (last updated: {last_updated_date})")

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
        if end_date >= date.today():
            raise ValueError("End date must be in the past")

        return start_date, end_date

    def clean_existing_reports(self):
        OverallReport.objects.all().delete()

    def process_date_range_incremental(self, start_date, end_date):
        """Process date range incrementally with bulk operations"""
        current_date = start_date
        processed_days = 0
        total_start_time = time.time()

        # Track all reports that get updated/created
        self.all_processed_reports = set()

        while current_date <= end_date:
            if self.verbose:
                self.stdout.write(f"\n📊 Processing {current_date}...")
            
            day_start_time = time.time()
            new_users_count = self.process_single_date_incremental(current_date)
            day_time = time.time() - day_start_time
            
            if self.verbose:
                if new_users_count > 0:
                    self.stdout.write(f"   ✅ Processed {new_users_count} new users in {day_time:.2f}s")
                else:
                    self.stdout.write(f"   ⏭️  No new users in {day_time:.2f}s")
            
            current_date += timedelta(days=1)
            processed_days += 1
            
            if processed_days % 10 == 0:
                self.stdout.write(f"📦 Processed {processed_days} days...")

        total_time = time.time() - total_start_time
        if self.verbose and processed_days > 0:
            self.stdout.write(f"   🎯 Completed {processed_days} days in {total_time:.2f}s")
        
        return processed_days

    def process_single_date_incremental(self, current_date):
        """Process a single date with bulk operations"""
        # Get new users for the date
        new_users = Petitioner.objects.filter(
            date_joined__date=current_date
        ).exclude(
            village__isnull=True
        ).select_related(
            'village', 'village__subdistrict',
            'village__subdistrict__district', 
            'village__subdistrict__district__state',
            'village__subdistrict__district__state__country'
        ).only(
            'id', 'first_name', 'last_name', 'village_id',
            'village__subdistrict_id', 'village__subdistrict__district_id',
            'village__subdistrict__district__state_id', 
            'village__subdistrict__district__state__country_id'
        )

        if not new_users.exists():
            return 0

        # Group users by geographic hierarchy and collect IDs for name lookup
        geo_hierarchy = {}
        users_by_village = defaultdict(list)
        village_ids = set()
        subdistrict_ids = set()
        district_ids = set()
        state_ids = set()
        country_ids = set()
        
        for user in new_users:
            village = user.village
            subdistrict = village.subdistrict
            district = subdistrict.district
            state = district.state
            country = state.country

            village_ids.add(village.id)
            subdistrict_ids.add(subdistrict.id)
            district_ids.add(district.id)
            state_ids.add(state.id)
            country_ids.add(country.id)

            geo_hierarchy[village.id] = {
                'subdistrict_id': subdistrict.id,
                'district_id': district.id,
                'state_id': state.id,
                'country_id': country.id
            }
            
            users_by_village[village.id].append(user)

        # Pre-fetch names only for entities we actually need
        self.prefetch_geo_names(village_ids, subdistrict_ids, district_ids, state_ids, country_ids)

        # Process all levels with bulk operations
        with transaction.atomic():
            village_reports = self.process_villages_bulk(current_date, users_by_village)
            subdistrict_reports = self.process_subdistricts_bulk(current_date, users_by_village, geo_hierarchy)
            district_reports = self.process_districts_bulk(current_date, users_by_village, geo_hierarchy)
            state_reports = self.process_states_bulk(current_date, users_by_village, geo_hierarchy)
            country_reports = self.process_countries_bulk(current_date, users_by_village, geo_hierarchy)
            
            # Track all processed reports for last_updated update
            self.track_processed_reports(village_reports, subdistrict_reports, district_reports, state_reports, country_reports)
            
            # Update parent IDs
            self.update_parent_ids_bulk(village_reports, subdistrict_reports, district_reports, state_reports, country_reports, geo_hierarchy)

        return len(new_users)

    def track_processed_reports(self, village_reports, subdistrict_reports, district_reports, state_reports, country_reports):
        """Track all reports that were processed for last_updated update"""
        for reports_dict in [village_reports, subdistrict_reports, district_reports, state_reports, country_reports]:
            for report in reports_dict.values():
                self.all_processed_reports.add(report.id)

    def update_last_updated_timestamp(self):
        """Update last_updated timestamp for all processed reports"""
        if not self.all_processed_reports:
            return
            
        current_time = datetime.now(pytz.UTC)
        updated_count = OverallReport.objects.filter(
            id__in=list(self.all_processed_reports)
        ).update(last_updated=current_time)
        
        if self.verbose:
            self.stdout.write(f"🕒 Updated last_updated timestamp for {updated_count} reports")

    def prefetch_geo_names(self, village_ids, subdistrict_ids, district_ids, state_ids, country_ids):
        """Prefetch geographic names only for entities we actually need"""
        if village_ids:
            villages = Village.objects.filter(id__in=village_ids).only('id', 'name')
            self.village_names.update({v.id: v.name for v in villages})
        
        if subdistrict_ids:
            subdistricts = Subdistrict.objects.filter(id__in=subdistrict_ids).only('id', 'name')
            self.subdistrict_names.update({s.id: s.name for s in subdistricts})
        
        if district_ids:
            districts = District.objects.filter(id__in=district_ids).only('id', 'name')
            self.district_names.update({d.id: d.name for d in districts})
        
        if state_ids:
            states = State.objects.filter(id__in=state_ids).only('id', 'name')
            self.state_names.update({s.id: s.name for s in states})
        
        if country_ids:
            countries = Country.objects.filter(id__in=country_ids).only('id', 'name')
            self.country_names.update({c.id: c.name for c in countries})

    def get_village_name(self, village_id):
        """Get village name - fetch if not cached"""
        if village_id not in self.village_names:
            try:
                village = Village.objects.only('name').get(id=village_id)
                self.village_names[village_id] = village.name
            except Village.DoesNotExist:
                self.village_names[village_id] = "Unknown Village"
        return self.village_names[village_id]

    def get_subdistrict_name(self, subdistrict_id):
        """Get subdistrict name - fetch if not cached"""
        if subdistrict_id not in self.subdistrict_names:
            try:
                subdistrict = Subdistrict.objects.only('name').get(id=subdistrict_id)
                self.subdistrict_names[subdistrict_id] = subdistrict.name
            except Subdistrict.DoesNotExist:
                self.subdistrict_names[subdistrict_id] = "Unknown Subdistrict"
        return self.subdistrict_names[subdistrict_id]

    def get_district_name(self, district_id):
        """Get district name - fetch if not cached"""
        if district_id not in self.district_names:
            try:
                district = District.objects.only('name').get(id=district_id)
                self.district_names[district_id] = district.name
            except District.DoesNotExist:
                self.district_names[district_id] = "Unknown District"
        return self.district_names[district_id]

    def get_state_name(self, state_id):
        """Get state name - fetch if not cached"""
        if state_id not in self.state_names:
            try:
                state = State.objects.only('name').get(id=state_id)
                self.state_names[state_id] = state.name
            except State.DoesNotExist:
                self.state_names[state_id] = "Unknown State"
        return self.state_names[state_id]

    def get_country_name(self, country_id):
        """Get country name - fetch if not cached"""
        if country_id not in self.country_names:
            try:
                country = Country.objects.only('name').get(id=country_id)
                self.country_names[country_id] = country.name
            except Country.DoesNotExist:
                self.country_names[country_id] = "Unknown Country"
        return self.country_names[country_id]

    def process_villages_bulk(self, current_date, users_by_village):
        """Process village reports with bulk operations"""
        village_ids = list(users_by_village.keys())
        if not village_ids:
            return {}

        # Get existing reports
        existing_reports = {
            report.geographical_entity: report 
            for report in OverallReport.objects.filter(
                level='village', 
                geographical_entity__in=village_ids
            )
        }

        reports_to_create = []
        reports_to_update = []
        reports_created = {}

        for village_id, users in users_by_village.items():
            count = len(users)
            user_data = {
                str(user.id): {
                    'id': str(user.id),
                    'name': f"{user.first_name} {user.last_name}"
                } for user in users
            }
            village_name = self.get_village_name(village_id)

            if village_id in existing_reports:
                report = existing_reports[village_id]
                report.total_users += count
                report.name = village_name
                
                # Update user data
                current_data = report.data or {}
                current_data.update(user_data)
                report.data = current_data
                
                # Update last30daysdata
                last30 = report.last30daysdata or {}
                last30[str(current_date)] = count
                report.last30daysdata = self.clean_last30days(last30, current_date)
                
                reports_to_update.append(report)
            else:
                report = OverallReport(
                    level='village',
                    geographical_entity=village_id,
                    name=village_name,
                    total_users=count,
                    data=user_data,
                    last30daysdata={str(current_date): count}
                )
                reports_to_create.append(report)
            
            reports_created[village_id] = report

        # Bulk operations
        if reports_to_create:
            created_reports = OverallReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
            # Track newly created reports
            for report in created_reports:
                self.all_processed_reports.add(report.id)
                
        if reports_to_update:
            OverallReport.objects.bulk_update(
                reports_to_update, 
                ['name', 'total_users', 'data', 'last30daysdata'],
                batch_size=self.batch_size
            )
            # Track updated reports
            for report in reports_to_update:
                self.all_processed_reports.add(report.id)

        return reports_created

    def process_subdistricts_bulk(self, current_date, users_by_village, geo_hierarchy):
        """Process subdistrict reports with bulk operations"""
        subdistrict_data = defaultdict(int)
        subdistrict_ids = set()
        
        for village_id, users in users_by_village.items():
            subdistrict_id = geo_hierarchy.get(village_id, {}).get('subdistrict_id')
            if subdistrict_id:
                subdistrict_data[subdistrict_id] += len(users)
                subdistrict_ids.add(subdistrict_id)

        # Ensure names are cached
        if subdistrict_ids:
            subdistricts = Subdistrict.objects.filter(id__in=subdistrict_ids).only('id', 'name')
            self.subdistrict_names.update({s.id: s.name for s in subdistricts})

        return self.process_higher_level_bulk(
            current_date, 'subdistrict', subdistrict_data, self.get_subdistrict_name
        )

    def process_districts_bulk(self, current_date, users_by_village, geo_hierarchy):
        """Process district reports with bulk operations"""
        district_data = defaultdict(int)
        district_ids = set()
        
        for village_id, users in users_by_village.items():
            district_id = geo_hierarchy.get(village_id, {}).get('district_id')
            if district_id:
                district_data[district_id] += len(users)
                district_ids.add(district_id)

        # Ensure names are cached
        if district_ids:
            districts = District.objects.filter(id__in=district_ids).only('id', 'name')
            self.district_names.update({d.id: d.name for d in districts})

        return self.process_higher_level_bulk(
            current_date, 'district', district_data, self.get_district_name
        )

    def process_states_bulk(self, current_date, users_by_village, geo_hierarchy):
        """Process state reports with bulk operations"""
        state_data = defaultdict(int)
        state_ids = set()
        
        for village_id, users in users_by_village.items():
            state_id = geo_hierarchy.get(village_id, {}).get('state_id')
            if state_id:
                state_data[state_id] += len(users)
                state_ids.add(state_id)

        # Ensure names are cached
        if state_ids:
            states = State.objects.filter(id__in=state_ids).only('id', 'name')
            self.state_names.update({s.id: s.name for s in states})

        return self.process_higher_level_bulk(
            current_date, 'state', state_data, self.get_state_name
        )

    def process_countries_bulk(self, current_date, users_by_village, geo_hierarchy):
        """Process country reports with bulk operations"""
        country_data = defaultdict(int)
        country_ids = set()
        
        for village_id, users in users_by_village.items():
            country_id = geo_hierarchy.get(village_id, {}).get('country_id')
            if country_id:
                country_data[country_id] += len(users)
                country_ids.add(country_id)

        # Ensure names are cached
        if country_ids:
            countries = Country.objects.filter(id__in=country_ids).only('id', 'name')
            self.country_names.update({c.id: c.name for c in countries})

        return self.process_higher_level_bulk(
            current_date, 'country', country_data, self.get_country_name
        )

    def process_higher_level_bulk(self, current_date, level, entity_data, name_getter):
        """Generic method to process higher level reports with bulk operations"""
        entity_ids = list(entity_data.keys())
        if not entity_ids:
            return {}

        # Get existing reports
        existing_reports = {
            report.geographical_entity: report 
            for report in OverallReport.objects.filter(
                level=level, 
                geographical_entity__in=entity_ids
            )
        }

        reports_to_create = []
        reports_to_update = []
        reports_created = {}

        for entity_id, count in entity_data.items():
            entity_name = name_getter(entity_id)

            if entity_id in existing_reports:
                report = existing_reports[entity_id]
                report.total_users += count
                report.name = entity_name
                report.last30daysdata = self.update_last30days(report.last30daysdata, current_date, count)
                reports_to_update.append(report)
            else:
                report = OverallReport(
                    level=level,
                    geographical_entity=entity_id,
                    name=entity_name,
                    total_users=count,
                    data={},
                    last30daysdata={str(current_date): count}
                )
                reports_to_create.append(report)
            
            reports_created[entity_id] = report

        # Bulk operations
        if reports_to_create:
            created_reports = OverallReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
            # Track newly created reports
            for report in created_reports:
                self.all_processed_reports.add(report.id)
                
        if reports_to_update:
            OverallReport.objects.bulk_update(
                reports_to_update, 
                ['name', 'total_users', 'last30daysdata'],
                batch_size=self.batch_size
            )
            # Track updated reports
            for report in reports_to_update:
                self.all_processed_reports.add(report.id)

        return reports_created

    def update_parent_ids_bulk(self, village_reports, subdistrict_reports, district_reports, state_reports, country_reports, geo_hierarchy):
        """Update parent IDs in bulk"""
        if self.verbose and (village_reports or subdistrict_reports or district_reports or state_reports):
            self.stdout.write("   🔗 Updating parent IDs...")
        
        # Update village -> subdistrict parent IDs
        villages_to_update = []
        for village_id, report in village_reports.items():
            subdistrict_id = geo_hierarchy.get(village_id, {}).get('subdistrict_id')
            if subdistrict_id and subdistrict_id in subdistrict_reports:
                parent_report = subdistrict_reports[subdistrict_id]
                if report.parent_id != parent_report.id:
                    report.parent_id = parent_report.id
                    villages_to_update.append(report)
                    self.all_processed_reports.add(report.id)
        
        if villages_to_update:
            OverallReport.objects.bulk_update(villages_to_update, ['parent_id'], batch_size=self.batch_size)

    def clean_last30days(self, last30days, current_date):
        """Clean last30days data to only include last 30 days"""
        if not last30days:
            return {}
        cutoff = current_date - timedelta(days=30)
        return {d: c for d, c in last30days.items() if date.fromisoformat(d) > cutoff}

    def update_last30days(self, last30days, current_date, count):
        """Update last30days data with new count"""
        current_data = last30days or {}
        current_data[str(current_date)] = count
        return self.clean_last30days(current_data, current_date)

    def rebuild_parent_data_with_all_children(self):
        """Rebuild parent data fields with ALL children (including zeros)"""
        self.stdout.write("🔄 Rebuilding parent data fields with ALL children...")
        start_time = time.time()
        
        level_map = [
            ('subdistrict', 'village', Village, 'subdistrict_id'),
            ('district', 'subdistrict', Subdistrict, 'district_id'),
            ('state', 'district', District, 'state_id'),
            ('country', 'state', State, 'country_id')
        ]

        total_updated = 0
        
        for parent_level, child_level, child_model, parent_fk in level_map:
            if self.verbose:
                self.stdout.write(f"   Processing {parent_level} level...")
            
            # Get all children grouped by parent
            children_by_parent = defaultdict(list)
            for child in child_model.objects.all().values('id', 'name', parent_fk):
                children_by_parent[child[parent_fk]].append({
                    'id': child['id'],
                    'name': child['name']
                })

            # Get all child reports
            child_reports = {
                r.geographical_entity: r
                for r in OverallReport.objects.filter(level=child_level)
            }

            # Get all parent reports
            parent_reports = OverallReport.objects.filter(level=parent_level)
            to_update = []

            for parent_report in parent_reports:
                parent_geo_id = parent_report.geographical_entity
                children_data = {}
                
                for child in children_by_parent.get(parent_geo_id, []):
                    child_report = child_reports.get(child['id'])
                    children_data[str(child['id'])] = {
                        'id': str(child['id']),
                        'name': child['name'],
                        'total_users': child_report.total_users if child_report else 0,
                        'report_id': str(child_report.id) if child_report else None
                    }
                
                if parent_report.data != children_data:
                    parent_report.data = children_data
                    to_update.append(parent_report)
                    self.all_processed_reports.add(parent_report.id)

            if to_update:
                OverallReport.objects.bulk_update(to_update, ['data'], batch_size=self.batch_size)
                total_updated += len(to_update)
                if self.verbose:
                    self.stdout.write(f"     Updated {len(to_update)} {parent_level} reports")

        total_time = time.time() - start_time
        self.stdout.write(f"✅ Parent data fields rebuilt with ALL children ({total_updated} updated) in {total_time:.2f}s")