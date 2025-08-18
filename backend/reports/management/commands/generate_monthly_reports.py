from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
from dateutil.relativedelta import relativedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import (
    VillageMonthlyReport, SubdistrictMonthlyReport,
    DistrictMonthlyReport, StateMonthlyReport, CountryMonthlyReport,
    VillageDailyReport
)
from users.models.petitioners import Petitioner
from collections import defaultdict


class Command(BaseCommand):
    help = 'Generates monthly reports for all geographic levels (UUID-safe)'

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

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        self.stdout.write(f"Generating monthly reports from {start_date} to {end_date}")
        
        current_month_start = start_date
        processed_months = 0
        
        while current_month_start <= end_date:
            month = current_month_start.month
            year = current_month_start.year
            month_end = (current_month_start + relativedelta(months=1)) - relativedelta(days=1)
            
            self.stdout.write(f"Processing {year}-{month:02d} ({current_month_start} to {month_end})...")
            
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
                self.update_parent_ids(
                    village_reports, 
                    subdistrict_reports,
                    district_reports,
                    state_reports,
                    country_reports
                )
            
            current_month_start += relativedelta(months=1)
            processed_months += 1
            
            if processed_months % 3 == 0:
                self.stdout.write(f"Processed {processed_months} months...")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated monthly reports for {processed_months} months'
        ))

    def get_date_range(self, kwargs):
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
        
        return start_date, end_date

    def get_month_start(self, dt):
        return date(dt.year, dt.month, 1)

    def create_village_monthly_reports(self, month_start, month_end, month, year):
        daily_reports = VillageDailyReport.objects.filter(
            date__range=[month_start, month_end]
        ).select_related('village')
        
        village_data = defaultdict(lambda: {'users': 0, 'user_data': {}})
        
        for report in daily_reports:
            village_id = report.village_id
            village_data[village_id]['users'] += report.new_users
            # Convert UUID keys in user_data to strings for JSON safety
            for uid, info in report.user_data.items():
                village_data[village_id]['user_data'][str(uid)] = {
                    "id": str(info["id"]),
                    "name": info["name"]
                }
        
        reports_created = {}
        for village_id, data in village_data.items():
            if data['users'] == 0:
                continue
            
            village = Village.objects.get(id=village_id)
            report, _ = VillageMonthlyReport.objects.update_or_create(
                last_date=month_end,
                village=village,
                month=month,
                year=year,
                defaults={
                    'new_users': data['users'],
                    'user_data': data['user_data'],
                    'parent_id': None
                }
            )
            reports_created[village_id] = report
        
        VillageMonthlyReport.objects.filter(
            last_date=month_end,
            new_users=0
        ).delete()
        
        return reports_created

    def create_subdistrict_monthly_reports(self, month_end, month, year, village_reports):
        villages = Village.objects.select_related('subdistrict').all()
        subdistrict_villages = defaultdict(list)
        for village in villages:
            subdistrict_villages[village.subdistrict_id].append(village)
        
        reports_created = {}
        for subdistrict_id, villages in subdistrict_villages.items():
            subdistrict = Subdistrict.objects.get(id=subdistrict_id)
            village_data = {}
            total_users = 0
            
            for village in villages:
                report = village_reports.get(village.id)
                count = report.new_users if report else 0
                village_data[str(village.id)] = {
                    "id": str(village.id),
                    "name": village.name,
                    "new_users": count,
                    "report_id": str(report.id) if report else None
                }
                total_users += count
            
            if total_users == 0:
                SubdistrictMonthlyReport.objects.filter(
                    last_date=month_end,
                    subdistrict=subdistrict
                ).delete()
                continue
            
            report, _ = SubdistrictMonthlyReport.objects.update_or_create(
                last_date=month_end,
                subdistrict=subdistrict,
                month=month,
                year=year,
                defaults={
                    'new_users': total_users,
                    'village_data': village_data,
                    'parent_id': None
                }
            )
            reports_created[subdistrict_id] = report
        
        return reports_created

    def create_district_monthly_reports(self, month_end, month, year, subdistrict_reports):
        subdistricts = Subdistrict.objects.select_related('district').all()
        district_subdistricts = defaultdict(list)
        for sub in subdistricts:
            district_subdistricts[sub.district_id].append(sub)
        
        reports_created = {}
        for district_id, subdistricts in district_subdistricts.items():
            district = District.objects.get(id=district_id)
            subdistrict_data = {}
            total_users = 0
            
            for sub in subdistricts:
                report = subdistrict_reports.get(sub.id)
                count = report.new_users if report else 0
                subdistrict_data[str(sub.id)] = {
                    "id": str(sub.id),
                    "name": sub.name,
                    "new_users": count,
                    "report_id": str(report.id) if report else None
                }
                total_users += count
            
            if total_users == 0:
                DistrictMonthlyReport.objects.filter(
                    last_date=month_end,
                    district=district
                ).delete()
                continue
            
            report, _ = DistrictMonthlyReport.objects.update_or_create(
                last_date=month_end,
                district=district,
                month=month,
                year=year,
                defaults={
                    'new_users': total_users,
                    'subdistrict_data': subdistrict_data,
                    'parent_id': None
                }
            )
            reports_created[district_id] = report
        
        return reports_created

    def create_state_monthly_reports(self, month_end, month, year, district_reports):
        districts = District.objects.select_related('state').all()
        state_districts = defaultdict(list)
        for district in districts:
            state_districts[district.state_id].append(district)
        
        reports_created = {}
        for state_id, districts in state_districts.items():
            state = State.objects.get(id=state_id)
            district_data = {}
            total_users = 0
            
            for district in districts:
                report = district_reports.get(district.id)
                count = report.new_users if report else 0
                district_data[str(district.id)] = {
                    "id": str(district.id),
                    "name": district.name,
                    "new_users": count,
                    "report_id": str(report.id) if report else None
                }
                total_users += count
            
            if total_users == 0:
                StateMonthlyReport.objects.filter(
                    last_date=month_end,
                    state=state
                ).delete()
                continue
            
            report, _ = StateMonthlyReport.objects.update_or_create(
                last_date=month_end,
                state=state,
                month=month,
                year=year,
                defaults={
                    'new_users': total_users,
                    'district_data': district_data,
                    'parent_id': None
                }
            )
            reports_created[state_id] = report
        
        return reports_created

    def create_country_monthly_reports(self, month_end, month, year, state_reports):
        states = State.objects.select_related('country').all()
        country_states = defaultdict(list)
        for state in states:
            country_states[state.country_id].append(state)
        
        reports_created = {}
        for country_id, states in country_states.items():
            country = Country.objects.get(id=country_id)
            state_data = {}
            total_users = 0
            
            for state in states:
                report = state_reports.get(state.id)
                count = report.new_users if report else 0
                state_data[str(state.id)] = {
                    "id": str(state.id),
                    "name": state.name,
                    "new_users": count,
                    "report_id": str(report.id) if report else None
                }
                total_users += count
            
            if total_users == 0:
                CountryMonthlyReport.objects.filter(
                    last_date=month_end,
                    country=country
                ).delete()
                continue
            
            report, _ = CountryMonthlyReport.objects.update_or_create(
                last_date=month_end,
                country=country,
                month=month,
                year=year,
                defaults={
                    'new_users': total_users,
                    'state_data': state_data
                }
            )
            reports_created[country_id] = report
        
        return reports_created

    def update_parent_ids(self, village_reports, subdistrict_reports, 
                          district_reports, state_reports, country_reports):
        villages = Village.objects.filter(id__in=village_reports.keys()).select_related('subdistrict')
        for village_id, report in village_reports.items():
            village = next((v for v in villages if v.id == village_id), None)
            if village and village.subdistrict_id in subdistrict_reports:
                report.parent_id = subdistrict_reports[village.subdistrict_id].id
                report.save()

        subs = Subdistrict.objects.filter(id__in=subdistrict_reports.keys()).select_related('district')
        for subdistrict_id, report in subdistrict_reports.items():
            subdistrict = next((s for s in subs if s.id == subdistrict_id), None)
            if subdistrict and subdistrict.district_id in district_reports:
                report.parent_id = district_reports[subdistrict.district_id].id
                report.save()

        dists = District.objects.filter(id__in=district_reports.keys()).select_related('state')
        for district_id, report in district_reports.items():
            district = next((d for d in dists if d.id == district_id), None)
            if district and district.state_id in state_reports:
                report.parent_id = state_reports[district.state_id].id
                report.save()

        states = State.objects.filter(id__in=state_reports.keys()).select_related('country')
        for state_id, report in state_reports.items():
            state = next((s for s in states if s.id == state_id), None)
            if state and state.country_id in country_reports:
                report.parent_id = country_reports[state.country_id].id
                report.save()
