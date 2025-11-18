# reports/management/commands/generate_daily_reports.py

from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.db.models import Prefetch, Count
from datetime import date, timedelta
import time
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import (
    VillageDailyReport, SubdistrictDailyReport,
    DistrictDailyReport, StateDailyReport, CountryDailyReport
)
from users.models import Petitioner


class Command(BaseCommand):
    help = 'Generates daily reports for all geographic levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: first user date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: yesterday)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if report exists'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed timing information'
        )

    def handle(self, *args, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        start_date, end_date = self.get_date_range(kwargs)

        if start_date == end_date:
            if self.should_skip_date(start_date, kwargs['force']):
                self.stdout.write(self.style.WARNING(
                    f"Report for {start_date} already exists. Skipping. Use --force to regenerate."
                ))
                return
            self.generate_reports_for_date(start_date)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully generated daily report for {start_date}'
            ))
            return

        self.stdout.write(f"Generating reports from {start_date} to {end_date}")
        current_date = start_date
        processed_days = 0
        total_start_time = time.time()

        while current_date <= end_date:
            if not self.should_skip_date(current_date, kwargs['force']):
                day_start_time = time.time()
                self.generate_reports_for_date(current_date)
                day_time = time.time() - day_start_time
                processed_days += 1
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Completed {current_date} in {day_time:.2f}s (Total: {processed_days} days)"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"⏭️  Skipping {current_date} (already exists)"
                ))
            current_date += timedelta(days=1)

        total_time = time.time() - total_start_time
        self.stdout.write(self.style.SUCCESS(
            f'🎉 Successfully generated daily reports for {processed_days} days in {total_time:.2f}s'
        ))

    def get_date_range(self, kwargs):
        self.stdout.write("📅 Determining date range...")
        first_user = Petitioner.objects.order_by('date_joined').first()
        default_start = first_user.date_joined.date() if first_user else date.today()

        start_date = (
            date.fromisoformat(kwargs['start_date'])
            if kwargs.get('start_date')
            else default_start
        )
        end_date = (
            date.fromisoformat(kwargs['end_date'])
            if kwargs.get('end_date')
            else date.today() - timedelta(days=1)
        )

        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date >= date.today():
            raise ValueError("End date must be in the past")

        self.stdout.write(f"   Start date: {start_date}")
        self.stdout.write(f"   End date: {end_date}")
        self.stdout.write(f"   Total days: {(end_date - start_date).days + 1}")
        return start_date, end_date

    def should_skip_date(self, report_date, force=False):
        if force:
            return False
        return CountryDailyReport.objects.filter(date=report_date).exists()

    def generate_reports_for_date(self, report_date):
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"📊 Processing {report_date}")
        self.stdout.write(f"{'='*60}")
        
        total_start_time = time.time()
        
        with transaction.atomic():
            # Village level
            village_start = time.time()
            village_reports = self.create_village_reports(report_date)
            village_time = time.time() - village_start
            
            # Subdistrict level
            subdistrict_start = time.time()
            subdistrict_reports = self.create_subdistrict_reports(report_date, village_reports)
            subdistrict_time = time.time() - subdistrict_start
            
            # District level
            district_start = time.time()
            district_reports = self.create_district_reports(report_date, subdistrict_reports)
            district_time = time.time() - district_start
            
            # State level
            state_start = time.time()
            state_reports = self.create_state_reports(report_date, district_reports)
            state_time = time.time() - state_start
            
            # Country level
            country_start = time.time()
            country_reports = self.create_country_reports(report_date, state_reports)
            country_time = time.time() - country_start
        
        total_time = time.time() - total_start_time
        
        # Summary
        self.stdout.write(f"\n📈 {report_date} SUMMARY:")
        self.stdout.write(f"   🏠 Villages: {len(village_reports)} reports ({village_time:.2f}s)")
        self.stdout.write(f"   🗺️  Subdistricts: {len(subdistrict_reports)} reports ({subdistrict_time:.2f}s)")
        self.stdout.write(f"   🏛️  Districts: {len(district_reports)} reports ({district_time:.2f}s)")
        self.stdout.write(f"   🌍 States: {len(state_reports)} reports ({state_time:.2f}s)")
        self.stdout.write(f"   🌐 Countries: {len(country_reports)} reports ({country_time:.2f}s)")
        self.stdout.write(f"   ⚡ Total time: {total_time:.2f}s")
        
        if self.verbose:
            self.print_detailed_breakdown(report_date, village_reports, subdistrict_reports, 
                                        district_reports, state_reports, country_reports)

    def create_village_reports(self, report_date):
        self.stdout.write(f"\n🏠 Processing VILLAGE reports...")
        start_time = time.time()
        
        # Step 1: Get all petitioners for the date with their village information
        petitioner_query_start = time.time()
        petitioners = Petitioner.objects.filter(
            date_joined__date=report_date
        ).select_related('village').only(
            'id', 'first_name', 'last_name', 'village_id', 'village__name'
        )
        petitioner_count = petitioners.count()
        petitioner_query_time = time.time() - petitioner_query_start
        
        self.stdout.write(f"   📋 Found {petitioner_count} petitioners in {petitioner_query_time:.2f}s")
        
        if petitioner_count == 0:
            self.stdout.write("   ⏭️  No petitioners found, skipping village reports")
            return {}
        
        # Step 2: Group petitioners by village
        grouping_start = time.time()
        village_data = {}
        for petitioner in petitioners:
            village_id = petitioner.village_id
            if village_id not in village_data:
                village_data[village_id] = {
                    'village': petitioner.village,
                    'petitioners': [],
                    'count': 0
                }
            village_data[village_id]['petitioners'].append(petitioner)
            village_data[village_id]['count'] += 1
        grouping_time = time.time() - grouping_start
        
        self.stdout.write(f"   🔄 Grouped into {len(village_data)} villages in {grouping_time:.2f}s")
        
        # Step 3: Create village reports
        report_creation_start = time.time()
        village_reports = {}
        created_count = 0
        updated_count = 0
        
        for village_id, data in village_data.items():
            user_data = {
                str(petitioner.id): {
                    "id": str(petitioner.id),
                    "name": f"{petitioner.first_name} {petitioner.last_name}"
                } for petitioner in data['petitioners']
            }

            report, created = VillageDailyReport.objects.update_or_create(
                date=report_date,
                village=data['village'],
                defaults={
                    'new_users': data['count'],
                    'user_data': user_data
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
            village_reports[village_id] = report

        report_creation_time = time.time() - report_creation_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Village reports: {created_count} created, {updated_count} updated in {report_creation_time:.2f}s")
        self.stdout.write(f"   ✅ Completed village level in {total_time:.2f}s")
        
        return village_reports

    def create_subdistrict_reports(self, report_date, village_reports):
        self.stdout.write(f"\n🗺️  Processing SUBDISTRICT reports...")
        start_time = time.time()
        
        village_ids = list(village_reports.keys())
        self.stdout.write(f"   📍 Input: {len(village_ids)} villages with activity")
        
        # Get ALL subdistricts that have villages with activity
        active_subdistrict_ids = Village.objects.filter(
            id__in=village_ids
        ).values_list('subdistrict_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active subdistricts: {len(active_subdistrict_ids)}")

        if not active_subdistrict_ids:
            self.stdout.write("   ⏭️  No active subdistricts, skipping subdistrict reports")
            return {}

        # Get ALL subdistricts with ONLY their villages (not all villages in database)
        query_start = time.time()
        subdistricts = Subdistrict.objects.filter(
            id__in=active_subdistrict_ids
        ).prefetch_related(
            Prefetch('village_set', 
                    queryset=Village.objects.filter(subdistrict_id__in=active_subdistrict_ids).only('id', 'name', 'subdistrict_id'), 
                    to_attr='all_villages')
        ).only('id', 'name')
        
        subdistrict_count = subdistricts.count()
        query_time = time.time() - query_start
        
        self.stdout.write(f"   📋 Found {subdistrict_count} subdistricts with their villages in {query_time:.2f}s")

        # Create subdistrict reports with ALL villages in each subdistrict
        report_start = time.time()
        subdistrict_reports = {}
        village_ids_for_parent_update = []
        created_count = 0
        updated_count = 0
        
        for subdistrict in subdistricts:
            village_data = {}
            total_new_users = 0
            
            # Include ALL villages in this specific subdistrict only
            villages_in_subdistrict = Village.objects.filter(
                subdistrict_id=subdistrict.id
            ).only('id', 'name')
            
            for village in villages_in_subdistrict:
                village_report = village_reports.get(village.id)
                new_users = village_report.new_users if village_report else 0
                report_id = str(village_report.id) if village_report else None
                
                village_data[str(village.id)] = {
                    "id": str(village.id),
                    "name": village.name,
                    "new_users": new_users,
                    "report_id": report_id
                }
                
                if village_report:
                    total_new_users += new_users
                    village_ids_for_parent_update.append(village.id)

            # Create report even if total_new_users is 0 (to include all villages with zeros)
            report, created = SubdistrictDailyReport.objects.update_or_create(
                date=report_date,
                subdistrict=subdistrict,
                defaults={
                    'new_users': total_new_users,
                    'village_data': village_data
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
            subdistrict_reports[subdistrict.id] = report

        report_time = time.time() - report_start
        
        # Bulk update parent IDs
        parent_update_start = time.time()
        if village_ids_for_parent_update:
            updated_parents = VillageDailyReport.objects.filter(
                village__id__in=village_ids_for_parent_update,
                date=report_date
            ).update(parent_id=report.id)
            parent_update_time = time.time() - parent_update_start
            self.stdout.write(f"   🔗 Updated parent IDs for {updated_parents} village reports in {parent_update_time:.2f}s")
        else:
            parent_update_time = 0

        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Subdistrict reports: {created_count} created, {updated_count} updated in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed subdistrict level in {total_time:.2f}s")
        
        return subdistrict_reports

    def create_district_reports(self, report_date, subdistrict_reports):
        self.stdout.write(f"\n🏛️  Processing DISTRICT reports...")
        start_time = time.time()
        
        subdistrict_ids = list(subdistrict_reports.keys())
        self.stdout.write(f"   📍 Input: {len(subdistrict_ids)} subdistricts with activity")
        
        # Get ALL districts that have subdistricts with activity
        active_district_ids = Subdistrict.objects.filter(
            id__in=subdistrict_ids
        ).values_list('district_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active districts: {len(active_district_ids)}")

        if not active_district_ids:
            self.stdout.write("   ⏭️  No active districts, skipping district reports")
            return {}

        # Create district reports with ALL subdistricts in each district
        report_start = time.time()
        district_reports = {}
        subdistrict_ids_for_parent_update = []
        created_count = 0
        updated_count = 0
        
        for district_id in active_district_ids:
            # Get the district and ALL its subdistricts
            district = District.objects.get(id=district_id)
            subdistricts_in_district = Subdistrict.objects.filter(
                district_id=district_id
            ).only('id', 'name')
            
            subdistrict_data = {}
            total_new_users = 0
            
            # Include ALL subdistricts in this specific district only
            for subdistrict in subdistricts_in_district:
                subdistrict_report = subdistrict_reports.get(subdistrict.id)
                new_users = subdistrict_report.new_users if subdistrict_report else 0
                report_id = str(subdistrict_report.id) if subdistrict_report else None
                
                subdistrict_data[str(subdistrict.id)] = {
                    "id": str(subdistrict.id),
                    "name": subdistrict.name,
                    "new_users": new_users,
                    "report_id": report_id
                }
                
                if subdistrict_report:
                    total_new_users += new_users
                    subdistrict_ids_for_parent_update.append(subdistrict.id)

            # Create report even if total_new_users is 0 (to include all subdistricts with zeros)
            report, created = DistrictDailyReport.objects.update_or_create(
                date=report_date,
                district=district,
                defaults={
                    'new_users': total_new_users,
                    'subdistrict_data': subdistrict_data
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
            district_reports[district.id] = report

        report_time = time.time() - report_start
        
        # Bulk update parent IDs
        parent_update_start = time.time()
        if subdistrict_ids_for_parent_update:
            updated_parents = SubdistrictDailyReport.objects.filter(
                subdistrict__id__in=subdistrict_ids_for_parent_update,
                date=report_date
            ).update(parent_id=report.id)
            parent_update_time = time.time() - parent_update_start
            self.stdout.write(f"   🔗 Updated parent IDs for {updated_parents} subdistrict reports in {parent_update_time:.2f}s")
        else:
            parent_update_time = 0

        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 District reports: {created_count} created, {updated_count} updated in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed district level in {total_time:.2f}s")
        
        return district_reports

    def create_state_reports(self, report_date, district_reports):
        self.stdout.write(f"\n🌍 Processing STATE reports...")
        start_time = time.time()
        
        district_ids = list(district_reports.keys())
        self.stdout.write(f"   📍 Input: {len(district_ids)} districts with activity")
        
        # Get ALL states that have districts with activity
        active_state_ids = District.objects.filter(
            id__in=district_ids
        ).values_list('state_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active states: {len(active_state_ids)}")

        if not active_state_ids:
            self.stdout.write("   ⏭️  No active states, skipping state reports")
            return {}

        # Create state reports with ALL districts in each state
        report_start = time.time()
        state_reports = {}
        district_ids_for_parent_update = []
        created_count = 0
        updated_count = 0
        
        for state_id in active_state_ids:
            # Get the state and ALL its districts
            state = State.objects.get(id=state_id)
            districts_in_state = District.objects.filter(
                state_id=state_id
            ).only('id', 'name')
            
            district_data = {}
            total_new_users = 0
            
            # Include ALL districts in this specific state only
            for district in districts_in_state:
                district_report = district_reports.get(district.id)
                new_users = district_report.new_users if district_report else 0
                report_id = str(district_report.id) if district_report else None
                
                district_data[str(district.id)] = {
                    "id": str(district.id),
                    "name": district.name,
                    "new_users": new_users,
                    "report_id": report_id
                }
                
                if district_report:
                    total_new_users += new_users
                    district_ids_for_parent_update.append(district.id)

            # Create report even if total_new_users is 0 (to include all districts with zeros)
            report, created = StateDailyReport.objects.update_or_create(
                date=report_date,
                state=state,
                defaults={
                    'new_users': total_new_users,
                    'district_data': district_data
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
            state_reports[state.id] = report

        report_time = time.time() - report_start
        
        # Bulk update parent IDs
        parent_update_start = time.time()
        if district_ids_for_parent_update:
            updated_parents = DistrictDailyReport.objects.filter(
                district__id__in=district_ids_for_parent_update,
                date=report_date
            ).update(parent_id=report.id)
            parent_update_time = time.time() - parent_update_start
            self.stdout.write(f"   🔗 Updated parent IDs for {updated_parents} district reports in {parent_update_time:.2f}s")
        else:
            parent_update_time = 0

        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 State reports: {created_count} created, {updated_count} updated in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed state level in {total_time:.2f}s")
        
        return state_reports

    def create_country_reports(self, report_date, state_reports):
        self.stdout.write(f"\n🌐 Processing COUNTRY reports...")
        start_time = time.time()
        
        state_ids = list(state_reports.keys())
        self.stdout.write(f"   📍 Input: {len(state_ids)} states with activity")
        
        # Get ALL countries that have states with activity
        active_country_ids = State.objects.filter(
            id__in=state_ids
        ).values_list('country_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active countries: {len(active_country_ids)}")

        if not active_country_ids:
            self.stdout.write("   ⏭️  No active countries, skipping country reports")
            return {}

        # Create country reports with ALL states in each country
        report_start = time.time()
        country_reports = {}
        state_ids_for_parent_update = []
        created_count = 0
        updated_count = 0
        
        for country_id in active_country_ids:
            # Get the country and ALL its states
            country = Country.objects.get(id=country_id)
            states_in_country = State.objects.filter(
                country_id=country_id
            ).only('id', 'name')
            
            state_data = {}
            total_new_users = 0
            
            # Include ALL states in this specific country only
            for state in states_in_country:
                state_report = state_reports.get(state.id)
                new_users = state_report.new_users if state_report else 0
                report_id = str(state_report.id) if state_report else None
                
                state_data[str(state.id)] = {
                    "id": str(state.id),
                    "name": state.name,
                    "new_users": new_users,
                    "report_id": report_id
                }
                
                if state_report:
                    total_new_users += new_users
                    state_ids_for_parent_update.append(state.id)

            # Create report even if total_new_users is 0 (to include all states with zeros)
            report, created = CountryDailyReport.objects.update_or_create(
                date=report_date,
                country=country,
                defaults={
                    'new_users': total_new_users,
                    'state_data': state_data
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
            country_reports[country.id] = report

        report_time = time.time() - report_start
        
        # Bulk update parent IDs
        parent_update_start = time.time()
        if state_ids_for_parent_update:
            updated_parents = StateDailyReport.objects.filter(
                state__id__in=state_ids_for_parent_update,
                date=report_date
            ).update(parent_id=report.id)
            parent_update_time = time.time() - parent_update_start
            self.stdout.write(f"   🔗 Updated parent IDs for {updated_parents} state reports in {parent_update_time:.2f}s")
        else:
            parent_update_time = 0

        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Country reports: {created_count} created, {updated_count} updated in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed country level in {total_time:.2f}s")
        
        return country_reports

    def print_detailed_breakdown(self, report_date, village_reports, subdistrict_reports, 
                               district_reports, state_reports, country_reports):
        """Print detailed breakdown of the reports created"""
        self.stdout.write(f"\n📊 DETAILED BREAKDOWN for {report_date}:")
        
        # Village breakdown
        if village_reports:
            total_village_users = sum(report.new_users for report in village_reports.values())
            self.stdout.write(f"   🏠 VILLAGES: {len(village_reports)} villages, {total_village_users} users")
            for village_id, report in list(village_reports.items())[:5]:  # Show first 5
                self.stdout.write(f"      • {report.village.name}: {report.new_users} users")
            if len(village_reports) > 5:
                self.stdout.write(f"      ... and {len(village_reports) - 5} more villages")
        
        # Subdistrict breakdown
        if subdistrict_reports:
            total_subdistrict_users = sum(report.new_users for report in subdistrict_reports.values())
            total_villages_in_reports = sum(len(report.village_data) for report in subdistrict_reports.values())
            self.stdout.write(f"   🗺️  SUBDISTRICTS: {len(subdistrict_reports)} subdistricts, {total_subdistrict_users} users")
            self.stdout.write(f"   📊 Total villages in subdistrict reports: {total_villages_in_reports}")
        
        # District breakdown
        if district_reports:
            total_district_users = sum(report.new_users for report in district_reports.values())
            total_subdistricts_in_reports = sum(len(report.subdistrict_data) for report in district_reports.values())
            self.stdout.write(f"   🏛️  DISTRICTS: {len(district_reports)} districts, {total_district_users} users")
            self.stdout.write(f"   📊 Total subdistricts in district reports: {total_subdistricts_in_reports}")
        
        # State breakdown
        if state_reports:
            total_state_users = sum(report.new_users for report in state_reports.values())
            total_districts_in_reports = sum(len(report.district_data) for report in state_reports.values())
            self.stdout.write(f"   🌍 STATES: {len(state_reports)} states, {total_state_users} users")
            self.stdout.write(f"   📊 Total districts in state reports: {total_districts_in_reports}")
        
        # Country breakdown
        if country_reports:
            total_country_users = sum(report.new_users for report in country_reports.values())
            total_states_in_reports = sum(len(report.state_data) for report in country_reports.values())
            self.stdout.write(f"   🌐 COUNTRIES: {len(country_reports)} countries, {total_country_users} users")
            self.stdout.write(f"   📊 Total states in country reports: {total_states_in_reports}")