# reports/management/commands/generate_monthly_reports.py

from django.core.management.base import BaseCommand
from django.db import transaction, models
from datetime import date
from dateutil.relativedelta import relativedelta
import time
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import (
    VillageMonthlyReport, SubdistrictMonthlyReport,
    DistrictMonthlyReport, StateMonthlyReport, CountryMonthlyReport,
    VillageDailyReport
)
from users.models.petitioners import Petitioner
from collections import defaultdict
from django.db.models import Sum, Prefetch


class Command(BaseCommand):
    help = 'Generates monthly reports for all geographic levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: first user date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: last month)'
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
        self.stdout.write(f"📅 Generating monthly reports from {start_date} to {end_date}")

        current_month_start = start_date
        processed_months = 0
        total_start_time = time.time()

        while current_month_start <= end_date:
            month = current_month_start.month
            year = current_month_start.year
            month_end = (current_month_start + relativedelta(months=1)) - relativedelta(days=1)
            
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"📊 Processing {year}-{month:02d} ({current_month_start} to {month_end})")
            self.stdout.write(f"{'='*60}")

            month_start_time = time.time()
            
            with transaction.atomic():
                village_reports = self.create_village_monthly_reports(
                    current_month_start, month_end, month, year
                )
                subdistrict_reports = self.create_subdistrict_monthly_reports(
                    month_end, month, year, village_reports
                )
                district_reports = self.create_district_monthly_reports(
                    month_end, month, year, subdistrict_reports
                )
                state_reports = self.create_state_monthly_reports(
                    month_end, month, year, district_reports
                )
                country_reports = self.create_country_monthly_reports(
                    month_end, month, year, state_reports
                )
                self.update_parent_ids_bulk(
                    village_reports, 
                    subdistrict_reports,
                    district_reports,
                    state_reports,
                    country_reports
                )
            
            month_time = time.time() - month_start_time
            current_month_start += relativedelta(months=1)
            processed_months += 1

            self.stdout.write(self.style.SUCCESS(
                f"✓ Completed {year}-{month:02d} in {month_time:.2f}s (Total: {processed_months} months)"
            ))

        total_time = time.time() - total_start_time
        self.stdout.write(self.style.SUCCESS(
            f'🎉 Successfully generated monthly reports for {processed_months} months in {total_time:.2f}s'
        ))

    def get_date_range(self, kwargs):
        self.stdout.write("📅 Determining date range...")
        first_user = Petitioner.objects.order_by('date_joined').first()
        
        if not first_user:
            self.stdout.write(self.style.WARNING('No users found. Exiting.'))
            exit(0)
        
        first_date = first_user.date_joined.date()
        default_start = date(first_date.year, first_date.month, 1)
        
        today = date.today()
        last_month = today - relativedelta(months=1)
        default_end = date(last_month.year, last_month.month, 1)
        
        start_date = (
            self.get_month_start(date.fromisoformat(kwargs['start_date']))
            if kwargs.get('start_date') 
            else default_start
        )
        end_date = (
            self.get_month_start(date.fromisoformat(kwargs['end_date']))
            if kwargs.get('end_date') 
            else default_end
        )
        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")

        self.stdout.write(f"   Start date: {start_date}")
        self.stdout.write(f"   End date: {end_date}")
        self.stdout.write(f"   Total months: {(end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1}")
        
        return start_date, end_date

    def get_month_start(self, dt):
        """Get the first day of the month containing the given date"""
        return date(dt.year, dt.month, 1)

    def create_village_monthly_reports(self, month_start, month_end, month, year):
        self.stdout.write(f"\n🏠 Processing VILLAGE monthly reports...")
        start_time = time.time()
        
        # Use database aggregation to get village totals for the month
        query_start = time.time()
        village_totals = VillageDailyReport.objects.filter(
            date__range=[month_start, month_end]
        ).values('village_id').annotate(
            total_users=Sum('new_users')
        ).filter(total_users__gt=0)
        
        village_ids_with_data = [item['village_id'] for item in village_totals]
        query_time = time.time() - query_start
        self.stdout.write(f"   📋 Found {len(village_ids_with_data)} villages with activity in {query_time:.2f}s")

        if not village_ids_with_data:
            self.stdout.write("   ⏭️  No village activity found")
            return {}

        # Get village details and their daily reports in bulk
        villages_start = time.time()
        villages = Village.objects.filter(
            id__in=village_ids_with_data
        ).prefetch_related(
            Prefetch('villagedailyreport_set',
                    queryset=VillageDailyReport.objects.filter(
                        date__range=[month_start, month_end]
                    ).only('village_id', 'new_users', 'user_data'),
                    to_attr='monthly_daily_reports')
        ).only('id', 'name')
        
        villages_time = time.time() - villages_start
        self.stdout.write(f"   📋 Loaded {villages.count()} villages with daily reports in {villages_time:.2f}s")

        # Prepare bulk operations
        report_start = time.time()
        reports_to_create = []
        reports_to_update = []
        
        # Get existing reports for update
        existing_reports = {
            report.village_id: report 
            for report in VillageMonthlyReport.objects.filter(
                last_date=month_end,
                village_id__in=village_ids_with_data
            )
        }

        for village in villages:
            total_users = 0
            user_data = {}
            
            # Aggregate data from daily reports
            for daily_report in village.monthly_daily_reports:
                total_users += daily_report.new_users
                # Convert UUID keys in user_data to strings for JSON safety
                for uid, info in daily_report.user_data.items():
                    user_data[str(uid)] = {
                        "id": str(info["id"]),
                        "name": info["name"]
                    }

            if total_users == 0:
                continue

            report_data = {
                'new_users': total_users,
                'user_data': user_data,
                'parent_id': None
            }
            
            if village.id in existing_reports:
                existing_report = existing_reports[village.id]
                for key, value in report_data.items():
                    setattr(existing_report, key, value)
                reports_to_update.append(existing_report)
            else:
                reports_to_create.append(VillageMonthlyReport(
                    last_date=month_end,
                    village=village,
                    month=month,
                    year=year,
                    **report_data
                ))

        # Bulk operations
        if reports_to_create:
            VillageMonthlyReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
        if reports_to_update:
            VillageMonthlyReport.objects.bulk_update(
                reports_to_update, 
                ['new_users', 'user_data', 'parent_id'],
                batch_size=self.batch_size
            )

        # Delete zero-user reports
        delete_count = VillageMonthlyReport.objects.filter(
            last_date=month_end,
            new_users=0
        ).delete()[0]

        # Build reports dict for parent updates
        reports_created = {}
        all_reports = VillageMonthlyReport.objects.filter(
            last_date=month_end,
            village_id__in=village_ids_with_data
        )
        for report in all_reports:
            reports_created[report.village_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Village monthly reports: {len(reports_to_create)} created, {len(reports_to_update)} updated, {delete_count} deleted in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed village level in {total_time:.2f}s")

        return reports_created

    def create_subdistrict_monthly_reports(self, month_end, month, year, village_reports):
        self.stdout.write(f"\n🗺️  Processing SUBDISTRICT monthly reports...")
        start_time = time.time()
        
        village_ids = list(village_reports.keys())
        self.stdout.write(f"   📍 Input: {len(village_ids)} villages with activity")

        if not village_ids:
            self.stdout.write("   ⏭️  No active villages, skipping subdistrict monthly reports")
            return {}

        # Get subdistricts that have active villages
        query_start = time.time()
        active_subdistrict_ids = Village.objects.filter(
            id__in=village_ids
        ).values_list('subdistrict_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active subdistricts: {len(active_subdistrict_ids)}")
        query_time = time.time() - query_start

        if not active_subdistrict_ids:
            self.stdout.write("   ⏭️  No active subdistricts")
            return {}

        # Get all subdistricts with their villages in bulk
        subdistricts_start = time.time()
        subdistricts = Subdistrict.objects.filter(
            id__in=active_subdistrict_ids
        ).prefetch_related(
            Prefetch('village_set',
                    queryset=Village.objects.only('id', 'name', 'subdistrict_id'),
                    to_attr='all_villages')
        ).only('id', 'name')
        
        subdistricts_time = time.time() - subdistricts_start
        self.stdout.write(f"   📋 Loaded {subdistricts.count()} subdistricts with villages in {subdistricts_time:.2f}s")

        # Prepare bulk operations
        report_start = time.time()
        reports_to_create = []
        reports_to_update = []
        
        existing_reports = {
            report.subdistrict_id: report 
            for report in SubdistrictMonthlyReport.objects.filter(
                last_date=month_end,
                subdistrict_id__in=active_subdistrict_ids
            )
        }

        for subdistrict in subdistricts:
            village_data = {}
            total_users = 0
            
            for village in subdistrict.all_villages:
                village_report = village_reports.get(village.id)
                count = village_report.new_users if village_report else 0
                village_data[str(village.id)] = {
                    "id": str(village.id),
                    "name": village.name,
                    "new_users": count,
                    "report_id": str(village_report.id) if village_report else None
                }
                total_users += count

            report_data = {
                'new_users': total_users,
                'village_data': village_data,
                'parent_id': None
            }
            
            if subdistrict.id in existing_reports:
                existing_report = existing_reports[subdistrict.id]
                for key, value in report_data.items():
                    setattr(existing_report, key, value)
                reports_to_update.append(existing_report)
            else:
                reports_to_create.append(SubdistrictMonthlyReport(
                    last_date=month_end,
                    subdistrict=subdistrict,
                    month=month,
                    year=year,
                    **report_data
                ))

        # Bulk operations
        if reports_to_create:
            SubdistrictMonthlyReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
        if reports_to_update:
            SubdistrictMonthlyReport.objects.bulk_update(
                reports_to_update, 
                ['new_users', 'village_data', 'parent_id'],
                batch_size=self.batch_size
            )

        # Build reports dict
        reports_created = {}
        all_reports = SubdistrictMonthlyReport.objects.filter(
            last_date=month_end,
            subdistrict_id__in=active_subdistrict_ids
        )
        for report in all_reports:
            reports_created[report.subdistrict_id] = report

        report_time = time.time() - report_start
        total_time = time.time() - start_time
        
        self.stdout.write(f"   💾 Subdistrict monthly reports: {len(reports_to_create)} created, {len(reports_to_update)} updated in {report_time:.2f}s")
        self.stdout.write(f"   ✅ Completed subdistrict level in {total_time:.2f}s")

        return reports_created

    def create_district_monthly_reports(self, month_end, month, year, subdistrict_reports):
        self.stdout.write(f"\n🏛️  Processing DISTRICT monthly reports...")
        start_time = time.time()
        
        subdistrict_ids = list(subdistrict_reports.keys())
        self.stdout.write(f"   📍 Input: {len(subdistrict_ids)} subdistricts with activity")

        if not subdistrict_ids:
            self.stdout.write("   ⏭️  No active subdistricts, skipping district monthly reports")
            return {}

        # Get districts that have active subdistricts
        active_district_ids = Subdistrict.objects.filter(
            id__in=subdistrict_ids
        ).values_list('district_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active districts: {len(active_district_ids)}")

        if not active_district_ids:
            self.stdout.write("   ⏭️  No active districts")
            return {}

        # Get districts with subdistricts in bulk
        districts = District.objects.filter(
            id__in=active_district_ids
        ).prefetch_related(
            Prefetch('subdistrict_set',
                    queryset=Subdistrict.objects.only('id', 'name', 'district_id'),
                    to_attr='all_subdistricts')
        ).only('id', 'name')

        # Bulk operations
        reports_to_create = []
        reports_to_update = []
        
        existing_reports = {
            report.district_id: report 
            for report in DistrictMonthlyReport.objects.filter(
                last_date=month_end,
                district_id__in=active_district_ids
            )
        }

        for district in districts:
            subdistrict_data = {}
            total_users = 0
            
            for subdistrict in district.all_subdistricts:
                subdistrict_report = subdistrict_reports.get(subdistrict.id)
                count = subdistrict_report.new_users if subdistrict_report else 0
                subdistrict_data[str(subdistrict.id)] = {
                    "id": str(subdistrict.id),
                    "name": subdistrict.name,
                    "new_users": count,
                    "report_id": str(subdistrict_report.id) if subdistrict_report else None
                }
                total_users += count

            report_data = {
                'new_users': total_users,
                'subdistrict_data': subdistrict_data,
                'parent_id': None
            }
            
            if district.id in existing_reports:
                existing_report = existing_reports[district.id]
                for key, value in report_data.items():
                    setattr(existing_report, key, value)
                reports_to_update.append(existing_report)
            else:
                reports_to_create.append(DistrictMonthlyReport(
                    last_date=month_end,
                    district=district,
                    month=month,
                    year=year,
                    **report_data
                ))

        # Bulk operations
        if reports_to_create:
            DistrictMonthlyReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
        if reports_to_update:
            DistrictMonthlyReport.objects.bulk_update(
                reports_to_update, 
                ['new_users', 'subdistrict_data', 'parent_id'],
                batch_size=self.batch_size
            )

        # Build reports dict
        reports_created = {}
        all_reports = DistrictMonthlyReport.objects.filter(
            last_date=month_end,
            district_id__in=active_district_ids
        )
        for report in all_reports:
            reports_created[report.district_id] = report

        total_time = time.time() - start_time
        self.stdout.write(f"   💾 District monthly reports: {len(reports_to_create)} created, {len(reports_to_update)} updated in {total_time:.2f}s")

        return reports_created

    def create_state_monthly_reports(self, month_end, month, year, district_reports):
        self.stdout.write(f"\n🌍 Processing STATE monthly reports...")
        start_time = time.time()
        
        district_ids = list(district_reports.keys())
        self.stdout.write(f"   📍 Input: {len(district_ids)} districts with activity")

        if not district_ids:
            self.stdout.write("   ⏭️  No active districts, skipping state monthly reports")
            return {}

        # Get states that have active districts
        active_state_ids = District.objects.filter(
            id__in=district_ids
        ).values_list('state_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active states: {len(active_state_ids)}")

        if not active_state_ids:
            self.stdout.write("   ⏭️  No active states")
            return {}

        # Get states with districts in bulk
        states = State.objects.filter(
            id__in=active_state_ids
        ).prefetch_related(
            Prefetch('district_set',
                    queryset=District.objects.only('id', 'name', 'state_id'),
                    to_attr='all_districts')
        ).only('id', 'name')

        # Bulk operations
        reports_to_create = []
        reports_to_update = []
        
        existing_reports = {
            report.state_id: report 
            for report in StateMonthlyReport.objects.filter(
                last_date=month_end,
                state_id__in=active_state_ids
            )
        }

        for state in states:
            district_data = {}
            total_users = 0
            
            for district in state.all_districts:
                district_report = district_reports.get(district.id)
                count = district_report.new_users if district_report else 0
                district_data[str(district.id)] = {
                    "id": str(district.id),
                    "name": district.name,
                    "new_users": count,
                    "report_id": str(district_report.id) if district_report else None
                }
                total_users += count

            report_data = {
                'new_users': total_users,
                'district_data': district_data,
                'parent_id': None
            }
            
            if state.id in existing_reports:
                existing_report = existing_reports[state.id]
                for key, value in report_data.items():
                    setattr(existing_report, key, value)
                reports_to_update.append(existing_report)
            else:
                reports_to_create.append(StateMonthlyReport(
                    last_date=month_end,
                    state=state,
                    month=month,
                    year=year,
                    **report_data
                ))

        # Bulk operations
        if reports_to_create:
            StateMonthlyReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
        if reports_to_update:
            StateMonthlyReport.objects.bulk_update(
                reports_to_update, 
                ['new_users', 'district_data', 'parent_id'],
                batch_size=self.batch_size
            )

        # Build reports dict
        reports_created = {}
        all_reports = StateMonthlyReport.objects.filter(
            last_date=month_end,
            state_id__in=active_state_ids
        )
        for report in all_reports:
            reports_created[report.state_id] = report

        total_time = time.time() - start_time
        self.stdout.write(f"   💾 State monthly reports: {len(reports_to_create)} created, {len(reports_to_update)} updated in {total_time:.2f}s")

        return reports_created

    def create_country_monthly_reports(self, month_end, month, year, state_reports):
        self.stdout.write(f"\n🌐 Processing COUNTRY monthly reports...")
        start_time = time.time()
        
        state_ids = list(state_reports.keys())
        self.stdout.write(f"   📍 Input: {len(state_ids)} states with activity")

        if not state_ids:
            self.stdout.write("   ⏭️  No active states, skipping country monthly reports")
            return {}

        # Get countries that have active states
        active_country_ids = State.objects.filter(
            id__in=state_ids
        ).values_list('country_id', flat=True).distinct()
        
        self.stdout.write(f"   📍 Active countries: {len(active_country_ids)}")

        if not active_country_ids:
            self.stdout.write("   ⏭️  No active countries")
            return {}

        # Get countries with states in bulk
        countries = Country.objects.filter(
            id__in=active_country_ids
        ).prefetch_related(
            Prefetch('state_set',
                    queryset=State.objects.only('id', 'name', 'country_id'),
                    to_attr='all_states')
        ).only('id', 'name')

        # Bulk operations
        reports_to_create = []
        reports_to_update = []
        
        existing_reports = {
            report.country_id: report 
            for report in CountryMonthlyReport.objects.filter(
                last_date=month_end,
                country_id__in=active_country_ids
            )
        }

        for country in countries:
            state_data = {}
            total_users = 0
            
            for state in country.all_states:
                state_report = state_reports.get(state.id)
                count = state_report.new_users if state_report else 0
                state_data[str(state.id)] = {
                    "id": str(state.id),
                    "name": state.name,
                    "new_users": count,
                    "report_id": str(state_report.id) if state_report else None
                }
                total_users += count

            # Always create country report
            report_data = {
                'new_users': total_users,
                'state_data': state_data
            }
            
            if country.id in existing_reports:
                existing_report = existing_reports[country.id]
                for key, value in report_data.items():
                    setattr(existing_report, key, value)
                reports_to_update.append(existing_report)
            else:
                reports_to_create.append(CountryMonthlyReport(
                    last_date=month_end,
                    country=country,
                    month=month,
                    year=year,
                    **report_data
                ))

        # Bulk operations
        if reports_to_create:
            CountryMonthlyReport.objects.bulk_create(reports_to_create, batch_size=self.batch_size)
        if reports_to_update:
            CountryMonthlyReport.objects.bulk_update(
                reports_to_update, 
                ['new_users', 'state_data'],
                batch_size=self.batch_size
            )

        # Build reports dict
        reports_created = {}
        all_reports = CountryMonthlyReport.objects.filter(
            last_date=month_end,
            country_id__in=active_country_ids
        )
        for report in all_reports:
            reports_created[report.country_id] = report

        total_time = time.time() - start_time
        self.stdout.write(f"   💾 Country monthly reports: {len(reports_to_create)} created, {len(reports_to_update)} updated in {total_time:.2f}s")

        return reports_created

    def update_parent_ids_bulk(self, village_reports, subdistrict_reports,
                              district_reports, state_reports, country_reports):
        self.stdout.write(f"\n🔗 Updating parent IDs in bulk...")
        start_time = time.time()
        total_updated = 0

        # Update village parent IDs in bulk
        if village_reports and subdistrict_reports:
            villages_to_update = []
            for village_id, report in village_reports.items():
                village = Village.objects.get(id=village_id)
                if village.subdistrict_id in subdistrict_reports:
                    report.parent_id = subdistrict_reports[village.subdistrict_id].id
                    villages_to_update.append(report)
                    total_updated += 1
            
            if villages_to_update:
                VillageMonthlyReport.objects.bulk_update(
                    villages_to_update, ['parent_id'], batch_size=self.batch_size
                )

        # Update subdistrict parent IDs in bulk
        if subdistrict_reports and district_reports:
            subdistricts_to_update = []
            for subdistrict_id, report in subdistrict_reports.items():
                subdistrict = Subdistrict.objects.get(id=subdistrict_id)
                if subdistrict.district_id in district_reports:
                    report.parent_id = district_reports[subdistrict.district_id].id
                    subdistricts_to_update.append(report)
                    total_updated += 1
            
            if subdistricts_to_update:
                SubdistrictMonthlyReport.objects.bulk_update(
                    subdistricts_to_update, ['parent_id'], batch_size=self.batch_size
                )

        # Update district parent IDs in bulk
        if district_reports and state_reports:
            districts_to_update = []
            for district_id, report in district_reports.items():
                district = District.objects.get(id=district_id)
                if district.state_id in state_reports:
                    report.parent_id = state_reports[district.state_id].id
                    districts_to_update.append(report)
                    total_updated += 1
            
            if districts_to_update:
                DistrictMonthlyReport.objects.bulk_update(
                    districts_to_update, ['parent_id'], batch_size=self.batch_size
                )

        # Update state parent IDs in bulk
        if state_reports and country_reports:
            states_to_update = []
            for state_id, report in state_reports.items():
                state = State.objects.get(id=state_id)
                if state.country_id in country_reports:
                    report.parent_id = country_reports[state.country_id].id
                    states_to_update.append(report)
                    total_updated += 1
            
            if states_to_update:
                StateMonthlyReport.objects.bulk_update(
                    states_to_update, ['parent_id'], batch_size=self.batch_size
                )

        total_time = time.time() - start_time
        self.stdout.write(f"   ✅ Updated {total_updated} parent IDs in {total_time:.2f}s")