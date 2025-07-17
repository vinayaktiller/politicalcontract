from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import (
    VillageDailyReport, SubdistrictDailyReport,
    DistrictDailyReport, StateDailyReport, CountryDailyReport
)
from users.models import Petitioner
from collections import defaultdict

class Command(BaseCommand):
    help = 'Generates daily reports for all geographic levels from first user date until yesterday'

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

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        self.stdout.write(f"Generating reports from {start_date} to {end_date}")
        
        current_date = start_date
        processed_days = 0
        
        while current_date <= end_date:
            self.stdout.write(f"Processing {current_date}...")
            
            with transaction.atomic():
                # Create reports bottom-up
                village_reports = self.create_village_reports(current_date)
                subdistrict_reports = self.create_subdistrict_reports(current_date, village_reports)
                district_reports = self.create_district_reports(current_date, subdistrict_reports)
                state_reports = self.create_state_reports(current_date, district_reports)
                self.create_country_reports(current_date, state_reports)
            
            current_date += timedelta(days=1)
            processed_days += 1
            
            if processed_days % 10 == 0:
                self.stdout.write(f"Processed {processed_days} days...")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated daily reports for {processed_days} days'
        ))

    def get_date_range(self, kwargs):
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
        
        return start_date, end_date

    def create_village_reports(self, report_date):
        users = Petitioner.objects.filter(
            date_joined__date=report_date
        ).exclude(
            village__isnull=True,
            subdistrict__isnull=True,
            district__isnull=True,
            state__isnull=True,
            country__isnull=True
        ).select_related('village')
        
        village_users = defaultdict(list)
        for user in users:
            village_users[user.village_id].append(user)
        
        village_reports = {}
        for village_id, users in village_users.items():
            village = Village.objects.get(id=village_id)
            user_data = {
                str(user.id): {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}"
                } for user in users
            }
            
            report, created = VillageDailyReport.objects.update_or_create(
                date=report_date,
                village=village,
                defaults={
                    'new_users': len(users),
                    'user_data': user_data
                }
            )
            village_reports[village_id] = report
        
        # Delete reports with zero users
        VillageDailyReport.objects.filter(
            date=report_date, 
            new_users=0
        ).delete()
            
        return village_reports

    def create_subdistrict_reports(self, report_date, village_reports):
        # Get all villages grouped by subdistrict
        villages = Village.objects.select_related('subdistrict').all()
        subdistrict_villages = defaultdict(list)
        for village in villages:
            subdistrict_villages[village.subdistrict_id].append(village)
        
        subdistrict_reports = {}
        for subdistrict_id, villages in subdistrict_villages.items():
            subdistrict = Subdistrict.objects.get(id=subdistrict_id)
            
            village_data = {}
            total_new_users = 0
            parent_report_id = None
            
            for village in villages:
                report = village_reports.get(village.id)
                village_data[str(village.id)] = {
                    "id": village.id,
                    "name": village.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": report.id if report else None
                }
                if report:
                    total_new_users += report.new_users
            
            # Only create report if there are new users
            if total_new_users > 0:
                report, created = SubdistrictDailyReport.objects.update_or_create(
                    date=report_date,
                    subdistrict=subdistrict,
                    defaults={
                        'new_users': total_new_users,
                        'village_data': village_data
                    }
                )
                subdistrict_reports[subdistrict_id] = report
                
                # Update village reports with parent ID
                for village in villages:
                    if village.id in village_reports:
                        village_report = village_reports[village.id]
                        village_report.parent_id = report.id
                        village_report.save()
            else:
                # Delete if exists
                SubdistrictDailyReport.objects.filter(
                    date=report_date,
                    subdistrict=subdistrict
                ).delete()
                
        return subdistrict_reports

    def create_district_reports(self, report_date, subdistrict_reports):
        # Get all subdistricts grouped by district
        subdistricts = Subdistrict.objects.select_related('district').all()
        district_subdistricts = defaultdict(list)
        for sub in subdistricts:
            district_subdistricts[sub.district_id].append(sub)
        
        district_reports = {}
        for district_id, subdistricts in district_subdistricts.items():
            district = District.objects.get(id=district_id)
            
            subdistrict_data = {}
            total_new_users = 0
            parent_report_id = None
            
            for sub in subdistricts:
                report = subdistrict_reports.get(sub.id)
                subdistrict_data[str(sub.id)] = {
                    "id": sub.id,
                    "name": sub.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": report.id if report else None
                }
                if report:
                    total_new_users += report.new_users
            
            # Only create report if there are new users
            if total_new_users > 0:
                report, created = DistrictDailyReport.objects.update_or_create(
                    date=report_date,
                    district=district,
                    defaults={
                        'new_users': total_new_users,
                        'subdistrict_data': subdistrict_data
                    }
                )
                district_reports[district_id] = report
                
                # Update subdistrict reports with parent ID
                for sub in subdistricts:
                    if sub.id in subdistrict_reports:
                        sub_report = subdistrict_reports[sub.id]
                        sub_report.parent_id = report.id
                        sub_report.save()
            else:
                # Delete if exists
                DistrictDailyReport.objects.filter(
                    date=report_date,
                    district=district
                ).delete()
                
        return district_reports

    def create_state_reports(self, report_date, district_reports):
        # Get all districts grouped by state
        districts = District.objects.select_related('state').all()
        state_districts = defaultdict(list)
        for district in districts:
            state_districts[district.state_id].append(district)
        
        state_reports = {}
        for state_id, districts in state_districts.items():
            state = State.objects.get(id=state_id)
            
            district_data = {}
            total_new_users = 0
            parent_report_id = None
            
            for district in districts:
                report = district_reports.get(district.id)
                district_data[str(district.id)] = {
                    "id": district.id,
                    "name": district.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": report.id if report else None
                }
                if report:
                    total_new_users += report.new_users
            
            # Only create report if there are new users
            if total_new_users > 0:
                report, created = StateDailyReport.objects.update_or_create(
                    date=report_date,
                    state=state,
                    defaults={
                        'new_users': total_new_users,
                        'district_data': district_data
                    }
                )
                state_reports[state_id] = report
                
                # Update district reports with parent ID
                for district in districts:
                    if district.id in district_reports:
                        dist_report = district_reports[district.id]
                        dist_report.parent_id = report.id
                        dist_report.save()
            else:
                # Delete if exists
                StateDailyReport.objects.filter(
                    date=report_date,
                    state=state
                ).delete()
                
        return state_reports

    def create_country_reports(self, report_date, state_reports):
        # Get all states grouped by country
        states = State.objects.select_related('country').all()
        country_states = defaultdict(list)
        for state in states:
            country_states[state.country_id].append(state)
        
        for country_id, states in country_states.items():
            country = Country.objects.get(id=country_id)
            
            state_data = {}
            total_new_users = 0
            
            for state in states:
                report = state_reports.get(state.id)
                state_data[str(state.id)] = {
                    "id": state.id,
                    "name": state.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": report.id if report else None
                }
                if report:
                    total_new_users += report.new_users
            
            # Only create report if there are new users
            if total_new_users > 0:
                report, created = CountryDailyReport.objects.update_or_create(
                    date=report_date,
                    country=country,
                    defaults={
                        'new_users': total_new_users,
                        'state_data': state_data
                    }
                )
                
                # Update state reports with parent ID
                for state in states:
                    if state.id in state_reports:
                        state_report = state_reports[state.id]
                        state_report.parent_id = report.id
                        state_report.save()
            else:
                # Delete if exists
                CountryDailyReport.objects.filter(
                    date=report_date,
                    country=country
                ).delete()