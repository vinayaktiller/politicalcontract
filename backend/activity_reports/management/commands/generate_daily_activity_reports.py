# reports/management/commands/generate_daily_activity_reports.py

from django.core.management.base import BaseCommand
from django.db import transaction, models
from datetime import date, timedelta
import time
from geographies.models.geos import Village, Subdistrict, District, State, Country
from activity_reports.models import (
    DailyVillageActivityReport,
    DailySubdistrictActivityReport,
    DailyDistrictActivityReport,
    DailyStateActivityReport,
    DailyCountryActivityReport,
    DailyActivitySummary
)
from users.models import Petitioner
from collections import defaultdict
from django.db.models import Prefetch


class Command(BaseCommand):
    help = 'Generates daily activity reports for all geographic levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: first activity date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: yesterday)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing reports'
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
        start_date, end_date = self.get_date_range(kwargs)
        force = kwargs['force']

        self.stdout.write(f"📅 Generating daily activity reports from {start_date} to {end_date}")
        if force:
            self.stdout.write("🔄 Force mode: Replacing existing reports")

        total_start_time = time.time()
        current_date = start_date
        processed_days = 0

        while current_date <= end_date:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"📊 Processing {current_date}")
            self.stdout.write(f"{'='*60}")

            day_start_time = time.time()
            
            try:
                daily_summary = DailyActivitySummary.objects.get(date=current_date)
            except DailyActivitySummary.DoesNotExist:
                self.stdout.write(f"⏭️  No activity data for {current_date}, skipping")
                current_date += timedelta(days=1)
                continue

            with transaction.atomic():
                if force:
                    self.delete_existing_reports(current_date)

                # Get active users for the day
                active_users_start = time.time()
                active_users = Petitioner.objects.filter(
                    id__in=daily_summary.active_users
                ).select_related(
                    'village', 'village__subdistrict',
                    'village__subdistrict__district',
                    'village__subdistrict__district__state',
                    'village__subdistrict__district__state__country'
                ).only(
                    'id', 'first_name', 'last_name', 'gender', 'age',
                    'village_id', 'village__subdistrict_id',
                    'village__subdistrict__district_id',
                    'village__subdistrict__district__state_id',
                    'village__subdistrict__district__state__country_id'
                )
                active_users_time = time.time() - active_users_start
                self.stdout.write(f"   📋 Found {active_users.count()} active users in {active_users_time:.2f}s")

                if active_users.exists():
                    # Process reports
                    village_reports = self.create_village_reports(current_date, active_users)
                    subdistrict_reports = self.create_subdistrict_reports(current_date, village_reports)
                    district_reports = self.create_district_reports(current_date, subdistrict_reports)
                    state_reports = self.create_state_reports(current_date, district_reports)
                    country_reports = self.create_country_reports(current_date, state_reports)

                    self.set_parent_ids_bulk(
                        village_reports, subdistrict_reports, 
                        district_reports, state_reports, country_reports
                    )
                else:
                    self.stdout.write("   ⏭️  No active users with geographic data")

            day_time = time.time() - day_start_time
            current_date += timedelta(days=1)
            processed_days += 1

            self.stdout.write(f"   ✅ Completed in {day_time:.2f}s")

            if processed_days % 10 == 0:
                self.stdout.write(f"📦 Processed {processed_days} days...")

        total_time = time.time() - total_start_time
        self.stdout.write(self.style.SUCCESS(
            f'🎉 Successfully generated daily activity reports for {processed_days} days in {total_time:.2f}s'
        ))

    def get_date_range(self, kwargs):
        self.stdout.write("📅 Determining date range...")
        first_activity = DailyActivitySummary.objects.order_by('date').first()
        if not first_activity:
            raise ValueError("No activity data found in database")

        default_start = first_activity.date
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

        self.stdout.write(f"   Start date: {start_date}")
        self.stdout.write(f"   End date: {end_date}")
        self.stdout.write(f"   Total days: {(end_date - start_date).days + 1}")
        
        return start_date, end_date

    def delete_existing_reports(self, report_date):
        self.stdout.write("   🗑️  Deleting existing reports...")
        delete_start = time.time()
        
        models_to_delete = [
            DailyVillageActivityReport,
            DailySubdistrictActivityReport,
            DailyDistrictActivityReport,
            DailyStateActivityReport,
            DailyCountryActivityReport
        ]
        
        total_deleted = 0
        for model in models_to_delete:
            deleted_count = model.objects.filter(date=report_date).delete()[0]
            total_deleted += deleted_count
        
        delete_time = time.time() - delete_start
        self.stdout.write(f"   ✅ Deleted {total_deleted} reports in {delete_time:.2f}s")

    def create_village_reports(self, report_date, active_users):
        self.stdout.write(f"\n🏠 Processing VILLAGE activity reports...")
        start_time = time.time()
        
        # Group users by village
        grouping_start = time.time()
        village_users = defaultdict(list)
        village_ids = set()
        
        for user in active_users:
            if user.village_id:
                village_users[user.village_id].append(user)
                village_ids.add(user.village_id)
        
        grouping_time = time.time() - grouping_start
        self.stdout.write(f"   🔄 Grouped {len(village_users)} villages in {grouping_time:.2f}s")

        if not village_ids:
            self.stdout.write("   ⏭️  No villages with active users")
            return {}

        # Get village names only for active villages
        village_names_start = time.time()
        villages = Village.objects.filter(
            id__in=village_ids
        ).only('id', 'name', 'subdistrict_id')
        village_name_map = {v.id: v.name for v in villages}
        village_subdistrict_map = {v.id: v.subdistrict_id for v in villages}
        village_names_time = time.time() - village_names_start
        
        self.stdout.write(f"   📋 Loaded {len(village_name_map)} village names in {village_names_time:.2f}s")

        # Create reports with bulk operations
        report_start = time.time()
        reports_to_create = []
        village_reports = {}

        for village_id, users in village_users.items():
            user_data = {}
            for user in users:
                user_data[str(user.id)] = {
                    "id": str(user.id),
                    "name": f"{user.first_name} {user.last_name}",
                    "gender": user.get_gender_display(),
                    "age": user.age
                }

            report = DailyVillageActivityReport(
                village_id=village_id,
                active_users=len(users),
                user_data=user_data,
                date=report_date
            )
            reports_to_create.append(report)
            village_reports[village_id] = report

        # Bulk create
        if reports_to_create:
            created_reports = DailyVillageActivityReport.objects.bulk_create(
                reports_to_create, batch_size=self.batch_size
            )
            # Update the dictionary with actual objects (with IDs)
            for report in created_reports:
                village_reports[report.village_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Created {len(reports_to_create)} village reports in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed village level in {total_time:.2f}s")

        # Store the subdistrict mapping for parent ID updates
        self.village_subdistrict_map = village_subdistrict_map
        
        return village_reports

    def create_subdistrict_reports(self, report_date, village_reports):
        self.stdout.write(f"\n🗺️  Processing SUBDISTRICT activity reports...")
        start_time = time.time()
        
        village_ids = list(village_reports.keys())
        self.stdout.write(f"   📍 Input: {len(village_ids)} villages with activity")

        if not village_ids:
            self.stdout.write("   ⏭️  No active villages, skipping subdistrict reports")
            return {}

        # Get subdistricts that have active villages
        subdistrict_ids = set(self.village_subdistrict_map.values())
        self.stdout.write(f"   📍 Active subdistricts: {len(subdistrict_ids)}")

        # Get subdistrict names and their villages
        subdistrict_start = time.time()
        subdistricts = Subdistrict.objects.filter(
            id__in=subdistrict_ids
        ).prefetch_related(
            Prefetch('village_set', 
                    queryset=Village.objects.filter(id__in=village_ids).only('id', 'name'),
                    to_attr='active_villages')
        ).only('id', 'name', 'district_id')
        
        subdistrict_name_map = {s.id: s.name for s in subdistricts}
        subdistrict_district_map = {s.id: s.district_id for s in subdistricts}
        subdistrict_time = time.time() - subdistrict_start
        
        self.stdout.write(f"   📋 Loaded {len(subdistricts)} subdistricts with villages in {subdistrict_time:.2f}s")

        # Create reports
        report_start = time.time()
        reports_to_create = []
        subdistrict_reports = {}

        for subdistrict in subdistricts:
            village_data = {}
            total_active_users = 0
            
            # Include ALL villages in this subdistrict (active and inactive)
            all_villages = Village.objects.filter(
                subdistrict_id=subdistrict.id
            ).only('id', 'name')
            
            for village in all_villages:
                village_report = village_reports.get(village.id)
                active_users = village_report.active_users if village_report else 0
                village_data[str(village.id)] = {
                    "id": str(village.id),
                    "name": village.name,
                    "active_users": active_users,
                    "report_id": str(village_report.id) if village_report else None
                }
                total_active_users += active_users

            if total_active_users > 0:
                report = DailySubdistrictActivityReport(
                    subdistrict_id=subdistrict.id,
                    active_users=total_active_users,
                    village_data=village_data,
                    date=report_date
                )
                reports_to_create.append(report)
                subdistrict_reports[subdistrict.id] = report

        # Bulk create
        if reports_to_create:
            created_reports = DailySubdistrictActivityReport.objects.bulk_create(
                reports_to_create, batch_size=self.batch_size
            )
            for report in created_reports:
                subdistrict_reports[report.subdistrict_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Created {len(reports_to_create)} subdistrict reports in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed subdistrict level in {total_time:.2f}s")

        # Store district mapping for parent ID updates
        self.subdistrict_district_map = subdistrict_district_map
        
        return subdistrict_reports

    def create_district_reports(self, report_date, subdistrict_reports):
        self.stdout.write(f"\n🏛️  Processing DISTRICT activity reports...")
        start_time = time.time()
        
        subdistrict_ids = list(subdistrict_reports.keys())
        self.stdout.write(f"   📍 Input: {len(subdistrict_ids)} subdistricts with activity")

        if not subdistrict_ids:
            self.stdout.write("   ⏭️  No active subdistricts, skipping district reports")
            return {}

        # Get districts that have active subdistricts
        district_ids = set(self.subdistrict_district_map.values())
        self.stdout.write(f"   📍 Active districts: {len(district_ids)}")

        # Get district names and their subdistricts
        district_start = time.time()
        districts = District.objects.filter(
            id__in=district_ids
        ).prefetch_related(
            Prefetch('subdistrict_set',
                    queryset=Subdistrict.objects.only('id', 'name'),
                    to_attr='all_subdistricts')
        ).only('id', 'name', 'state_id')
        
        district_name_map = {d.id: d.name for d in districts}
        district_state_map = {d.id: d.state_id for d in districts}
        district_time = time.time() - district_start
        
        self.stdout.write(f"   📋 Loaded {len(districts)} districts with subdistricts in {district_time:.2f}s")

        # Create reports
        report_start = time.time()
        reports_to_create = []
        district_reports = {}

        for district in districts:
            subdistrict_data = {}
            total_active_users = 0
            
            for subdistrict in district.all_subdistricts:
                subdistrict_report = subdistrict_reports.get(subdistrict.id)
                active_users = subdistrict_report.active_users if subdistrict_report else 0
                subdistrict_data[str(subdistrict.id)] = {
                    "id": str(subdistrict.id),
                    "name": subdistrict.name,
                    "active_users": active_users,
                    "report_id": str(subdistrict_report.id) if subdistrict_report else None
                }
                total_active_users += active_users

            if total_active_users > 0:
                report = DailyDistrictActivityReport(
                    district_id=district.id,
                    active_users=total_active_users,
                    subdistrict_data=subdistrict_data,
                    date=report_date
                )
                reports_to_create.append(report)
                district_reports[district.id] = report

        # Bulk create
        if reports_to_create:
            created_reports = DailyDistrictActivityReport.objects.bulk_create(
                reports_to_create, batch_size=self.batch_size
            )
            for report in created_reports:
                district_reports[report.district_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Created {len(reports_to_create)} district reports in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed district level in {total_time:.2f}s")

        # Store state mapping for parent ID updates
        self.district_state_map = district_state_map
        
        return district_reports

    def create_state_reports(self, report_date, district_reports):
        self.stdout.write(f"\n🌍 Processing STATE activity reports...")
        start_time = time.time()
        
        district_ids = list(district_reports.keys())
        self.stdout.write(f"   📍 Input: {len(district_ids)} districts with activity")

        if not district_ids:
            self.stdout.write("   ⏭️  No active districts, skipping state reports")
            return {}

        # Get states that have active districts
        state_ids = set(self.district_state_map.values())
        self.stdout.write(f"   📍 Active states: {len(state_ids)}")

        # Get state names and their districts
        state_start = time.time()
        states = State.objects.filter(
            id__in=state_ids
        ).prefetch_related(
            Prefetch('district_set',
                    queryset=District.objects.only('id', 'name'),
                    to_attr='all_districts')
        ).only('id', 'name', 'country_id')
        
        state_name_map = {s.id: s.name for s in states}
        state_country_map = {s.id: s.country_id for s in states}
        state_time = time.time() - state_start
        
        self.stdout.write(f"   📋 Loaded {len(states)} states with districts in {state_time:.2f}s")

        # Create reports
        report_start = time.time()
        reports_to_create = []
        state_reports = {}

        for state in states:
            district_data = {}
            total_active_users = 0
            
            for district in state.all_districts:
                district_report = district_reports.get(district.id)
                active_users = district_report.active_users if district_report else 0
                district_data[str(district.id)] = {
                    "id": str(district.id),
                    "name": district.name,
                    "active_users": active_users,
                    "report_id": str(district_report.id) if district_report else None
                }
                total_active_users += active_users

            if total_active_users > 0:
                report = DailyStateActivityReport(
                    state_id=state.id,
                    active_users=total_active_users,
                    district_data=district_data,
                    date=report_date
                )
                reports_to_create.append(report)
                state_reports[state.id] = report

        # Bulk create
        if reports_to_create:
            created_reports = DailyStateActivityReport.objects.bulk_create(
                reports_to_create, batch_size=self.batch_size
            )
            for report in created_reports:
                state_reports[report.state_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Created {len(reports_to_create)} state reports in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed state level in {total_time:.2f}s")

        # Store country mapping for parent ID updates
        self.state_country_map = state_country_map
        
        return state_reports

    def create_country_reports(self, report_date, state_reports):
        self.stdout.write(f"\n🌐 Processing COUNTRY activity reports...")
        start_time = time.time()
        
        state_ids = list(state_reports.keys())
        self.stdout.write(f"   📍 Input: {len(state_ids)} states with activity")

        if not state_ids:
            self.stdout.write("   ⏭️  No active states, skipping country reports")
            return {}

        # Get countries that have active states
        country_ids = set(self.state_country_map.values())
        self.stdout.write(f"   📍 Active countries: {len(country_ids)}")

        # Get country names and their states
        country_start = time.time()
        countries = Country.objects.filter(
            id__in=country_ids
        ).prefetch_related(
            Prefetch('state_set',
                    queryset=State.objects.only('id', 'name'),
                    to_attr='all_states')
        ).only('id', 'name')
        
        country_time = time.time() - country_start
        self.stdout.write(f"   📋 Loaded {len(countries)} countries with states in {country_time:.2f}s")

        # Create reports
        report_start = time.time()
        reports_to_create = []
        country_reports = {}

        for country in countries:
            state_data = {}
            total_active_users = 0
            
            for state in country.all_states:
                state_report = state_reports.get(state.id)
                active_users = state_report.active_users if state_report else 0
                state_data[str(state.id)] = {
                    "id": str(state.id),
                    "name": state.name,
                    "active_users": active_users,
                    "report_id": str(state_report.id) if state_report else None
                }
                total_active_users += active_users

            if total_active_users > 0:
                report = DailyCountryActivityReport(
                    country_id=country.id,
                    active_users=total_active_users,
                    state_data=state_data,
                    date=report_date
                )
                reports_to_create.append(report)
                country_reports[country.id] = report

        # Bulk create
        if reports_to_create:
            created_reports = DailyCountryActivityReport.objects.bulk_create(
                reports_to_create, batch_size=self.batch_size
            )
            for report in created_reports:
                country_reports[report.country_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Created {len(reports_to_create)} country reports in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed country level in {total_time:.2f}s")
        
        return country_reports

    def set_parent_ids_bulk(self, village_reports, subdistrict_reports,
                           district_reports, state_reports, country_reports):
        self.stdout.write(f"\n🔗 Setting parent IDs...")
        start_time = time.time()
        total_updated = 0

        # Update village -> subdistrict parent IDs
        villages_to_update = []
        for village_id, report in village_reports.items():
            subdistrict_id = self.village_subdistrict_map.get(village_id)
            if subdistrict_id and subdistrict_id in subdistrict_reports:
                report.parent_id = subdistrict_reports[subdistrict_id].id
                villages_to_update.append(report)
                total_updated += 1
        
        if villages_to_update:
            DailyVillageActivityReport.objects.bulk_update(
                villages_to_update, ['parent_id'], batch_size=self.batch_size
            )

        # Update subdistrict -> district parent IDs
        subdistricts_to_update = []
        for subdistrict_id, report in subdistrict_reports.items():
            district_id = self.subdistrict_district_map.get(subdistrict_id)
            if district_id and district_id in district_reports:
                report.parent_id = district_reports[district_id].id
                subdistricts_to_update.append(report)
                total_updated += 1
        
        if subdistricts_to_update:
            DailySubdistrictActivityReport.objects.bulk_update(
                subdistricts_to_update, ['parent_id'], batch_size=self.batch_size
            )

        # Update district -> state parent IDs
        districts_to_update = []
        for district_id, report in district_reports.items():
            state_id = self.district_state_map.get(district_id)
            if state_id and state_id in state_reports:
                report.parent_id = state_reports[state_id].id
                districts_to_update.append(report)
                total_updated += 1
        
        if districts_to_update:
            DailyDistrictActivityReport.objects.bulk_update(
                districts_to_update, ['parent_id'], batch_size=self.batch_size
            )

        # Update state -> country parent IDs
        states_to_update = []
        for state_id, report in state_reports.items():
            country_id = self.state_country_map.get(state_id)
            if country_id and country_id in country_reports:
                report.parent_id = country_reports[country_id].id
                states_to_update.append(report)
                total_updated += 1
        
        if states_to_update:
            DailyStateActivityReport.objects.bulk_update(
                states_to_update, ['parent_id'], batch_size=self.batch_size
            )

        total_time = time.time() - start_time
        self.stdout.write(f"   ✅ Updated {total_updated} parent IDs in {total_time:.2f}s")