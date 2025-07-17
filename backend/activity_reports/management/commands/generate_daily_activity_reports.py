# activity_reports/management/commands/generate_daily_activity_reports.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from activity_reports.models import (
    DailyVillageActivityReport,
    DailySubdistrictActivityReport,
    DailyDistrictActivityReport,
    DailyStateActivityReport,
    DailyCountryActivityReport
)
from users.models import Petitioner
from activity_reports.models import DailyActivitySummary
from collections import defaultdict

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

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        force = kwargs['force']
        
        self.stdout.write(f"Generating reports from {start_date} to {end_date}")
        if force:
            self.stdout.write("Force mode: Replacing existing reports")
        
        # Preload geographic hierarchy
        self.preload_geographic_data()
        
        current_date = start_date
        processed_days = 0
        
        while current_date <= end_date:
            self.stdout.write(f"Processing {current_date}...")
            
            try:
                daily_summary = DailyActivitySummary.objects.get(date=current_date)
            except DailyActivitySummary.DoesNotExist:
                self.stdout.write(f"No activity data for {current_date}, skipping")
                current_date += timedelta(days=1)
                continue
            
            with transaction.atomic():
                # Delete existing reports if forcing regeneration
                if force:
                    self.delete_existing_reports(current_date)
                
                # Get active users with geographic relationships
                active_users = Petitioner.objects.filter(
                    id__in=daily_summary.active_users
                ).select_related(
                    'village', 
                    'subdistrict',
                    'district',
                    'state',
                    'country'
                )
                
                # Create reports bottom-up
                village_reports = self.create_village_reports(current_date, active_users)
                subdistrict_reports = self.create_subdistrict_reports(current_date, village_reports)
                district_reports = self.create_district_reports(current_date, subdistrict_reports)
                state_reports = self.create_state_reports(current_date, district_reports)
                country_reports = self.create_country_reports(current_date, state_reports)
                
                # Set parent IDs after creating all reports
                self.set_parent_ids(
                    village_reports, 
                    subdistrict_reports, 
                    district_reports, 
                    state_reports, 
                    country_reports
                )
            
            current_date += timedelta(days=1)
            processed_days += 1
            
            if processed_days % 10 == 0:
                self.stdout.write(f"Processed {processed_days} days...")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated daily activity reports for {processed_days} days'
        ))

    def preload_geographic_data(self):
        """Preload all geographic entities for efficient hierarchy building"""
        self.villages = list(Village.objects.all().values('id', 'name', 'subdistrict_id'))
        self.villages_by_subdistrict = defaultdict(list)
        for v in self.villages:
            self.villages_by_subdistrict[v['subdistrict_id']].append(v)

        self.subdistricts = list(Subdistrict.objects.all().values('id', 'name', 'district_id'))
        self.subdistricts_by_district = defaultdict(list)
        for sd in self.subdistricts:
            self.subdistricts_by_district[sd['district_id']].append(sd)

        self.districts = list(District.objects.all().values('id', 'name', 'state_id'))
        self.districts_by_state = defaultdict(list)
        for d in self.districts:
            self.districts_by_state[d['state_id']].append(d)

        self.states = list(State.objects.all().values('id', 'name', 'country_id'))
        self.states_by_country = defaultdict(list)
        for s in self.states:
            self.states_by_country[s['country_id']].append(s)

        self.countries = list(Country.objects.all().values('id', 'name'))

    def delete_existing_reports(self, report_date):
        """Delete existing reports for a date"""
        DailyVillageActivityReport.objects.filter(date=report_date).delete()
        DailySubdistrictActivityReport.objects.filter(date=report_date).delete()
        DailyDistrictActivityReport.objects.filter(date=report_date).delete()
        DailyStateActivityReport.objects.filter(date=report_date).delete()
        DailyCountryActivityReport.objects.filter(date=report_date).delete()

    def get_date_range(self, kwargs):
        """Determine the date range for report generation"""
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
        
        return start_date, end_date

    def create_village_reports(self, report_date, active_users):
        """Create village reports only for villages with active users"""
        village_users = defaultdict(list)
        village_reports = {}
        
        # Group active users by village
        for user in active_users:
            if user.village_id:
                village_users[user.village_id].append(user)
        
        # Create reports only for villages with activity
        for village_id, users in village_users.items():
            user_data = {}
            for user in users:
                user_data[str(user.id)] = {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "gender": user.get_gender_display(),
                    "age": user.age
                }
            
            report = DailyVillageActivityReport.objects.create(
                village_id=village_id,
                active_users=len(users),
                user_data=user_data,
                date=report_date
            )
            village_reports[village_id] = report
        
        return village_reports

    def create_subdistrict_reports(self, report_date, village_reports):
        """Create subdistrict reports only for subdistricts with active users"""
        # Track active users per subdistrict
        subdistrict_activity = defaultdict(int)
        subdistrict_village_reports = defaultdict(dict)
        
        # Calculate activity and prepare village data
        for village in self.villages:
            subdistrict_id = village['subdistrict_id']
            village_id = village['id']
            
            if village_id in village_reports:
                # Village has activity
                report = village_reports[village_id]
                subdistrict_activity[subdistrict_id] += report.active_users
                subdistrict_village_reports[subdistrict_id][village_id] = {
                    "id": village_id,
                    "name": village['name'],
                    "active_users": report.active_users,
                    "report_id": report.id
                }
            else:
                # Village has no activity
                subdistrict_village_reports[subdistrict_id][village_id] = {
                    "id": village_id,
                    "name": village['name'],
                    "active_users": 0,
                    "report_id": None
                }
        
        # Create reports only for subdistricts with activity
        subdistrict_reports = {}
        for subdistrict_id, active_count in subdistrict_activity.items():
            if active_count > 0:
                report = DailySubdistrictActivityReport.objects.create(
                    subdistrict_id=subdistrict_id,
                    active_users=active_count,
                    village_data=subdistrict_village_reports[subdistrict_id],
                    date=report_date
                )
                subdistrict_reports[subdistrict_id] = report
        
        return subdistrict_reports

    def create_district_reports(self, report_date, subdistrict_reports):
        """Create district reports only for districts with active users"""
        # Track activity per district
        district_activity = defaultdict(int)
        district_subdistrict_reports = defaultdict(dict)
        
        # Calculate activity and prepare subdistrict data
        for subdistrict in self.subdistricts:
            district_id = subdistrict['district_id']
            subdistrict_id = subdistrict['id']
            
            if subdistrict_id in subdistrict_reports:
                # Subdistrict has activity
                report = subdistrict_reports[subdistrict_id]
                district_activity[district_id] += report.active_users
                district_subdistrict_reports[district_id][subdistrict_id] = {
                    "id": subdistrict_id,
                    "name": subdistrict['name'],
                    "active_users": report.active_users,
                    "report_id": report.id
                }
            else:
                # Subdistrict has no activity
                district_subdistrict_reports[district_id][subdistrict_id] = {
                    "id": subdistrict_id,
                    "name": subdistrict['name'],
                    "active_users": 0,
                    "report_id": None
                }
        
        # Create reports only for districts with activity
        district_reports = {}
        for district_id, active_count in district_activity.items():
            if active_count > 0:
                report = DailyDistrictActivityReport.objects.create(
                    district_id=district_id,
                    active_users=active_count,
                    subdistrict_data=district_subdistrict_reports[district_id],
                    date=report_date
                )
                district_reports[district_id] = report
        
        return district_reports

    def create_state_reports(self, report_date, district_reports):
        """Create state reports only for states with active users"""
        # Track activity per state
        state_activity = defaultdict(int)
        state_district_reports = defaultdict(dict)
        
        # Calculate activity and prepare district data
        for district in self.districts:
            state_id = district['state_id']
            district_id = district['id']
            
            if district_id in district_reports:
                # District has activity
                report = district_reports[district_id]
                state_activity[state_id] += report.active_users
                state_district_reports[state_id][district_id] = {
                    "id": district_id,
                    "name": district['name'],
                    "active_users": report.active_users,
                    "report_id": report.id
                }
            else:
                # District has no activity
                state_district_reports[state_id][district_id] = {
                    "id": district_id,
                    "name": district['name'],
                    "active_users": 0,
                    "report_id": None
                }
        
        # Create reports only for states with activity
        state_reports = {}
        for state_id, active_count in state_activity.items():
            if active_count > 0:
                report = DailyStateActivityReport.objects.create(
                    state_id=state_id,
                    active_users=active_count,
                    district_data=state_district_reports[state_id],
                    date=report_date
                )
                state_reports[state_id] = report
        
        return state_reports

    def create_country_reports(self, report_date, state_reports):
        """Create country reports only for countries with active users"""
        # Track activity per country
        country_activity = defaultdict(int)
        country_state_reports = defaultdict(dict)
        
        # Calculate activity and prepare state data
        for state in self.states:
            country_id = state['country_id']
            state_id = state['id']
            
            if state_id in state_reports:
                # State has activity
                report = state_reports[state_id]
                country_activity[country_id] += report.active_users
                country_state_reports[country_id][state_id] = {
                    "id": state_id,
                    "name": state['name'],
                    "active_users": report.active_users,
                    "report_id": report.id
                }
            else:
                # State has no activity
                country_state_reports[country_id][state_id] = {
                    "id": state_id,
                    "name": state['name'],
                    "active_users": 0,
                    "report_id": None
                }
        
        # Create reports only for countries with activity
        country_reports = {}
        for country_id, active_count in country_activity.items():
            if active_count > 0:
                report = DailyCountryActivityReport.objects.create(
                    country_id=country_id,
                    active_users=active_count,
                    state_data=country_state_reports[country_id],
                    date=report_date
                )
                country_reports[country_id] = report
        
        return country_reports

    def set_parent_ids(self, village_reports, subdistrict_reports, 
                      district_reports, state_reports, country_reports):
        """Set parent IDs for all reports after they're created"""
        # Set village parent IDs
        for village_id, report in village_reports.items():
            # Find subdistrict for this village
            for village_data in self.villages:
                if village_data['id'] == village_id:
                    subdistrict_id = village_data['subdistrict_id']
                    if subdistrict_id in subdistrict_reports:
                        report.parent_id = subdistrict_reports[subdistrict_id].id
                        report.save()
                    break
        
        # Set subdistrict parent IDs
        for subdistrict_id, report in subdistrict_reports.items():
            # Find district for this subdistrict
            for sub_data in self.subdistricts:
                if sub_data['id'] == subdistrict_id:
                    district_id = sub_data['district_id']
                    if district_id in district_reports:
                        report.parent_id = district_reports[district_id].id
                        report.save()
                    break
        
        # Set district parent IDs
        for district_id, report in district_reports.items():
            # Find state for this district
            for dist_data in self.districts:
                if dist_data['id'] == district_id:
                    state_id = dist_data['state_id']
                    if state_id in state_reports:
                        report.parent_id = state_reports[state_id].id
                        report.save()
                    break
        
        # Set state parent IDs
        for state_id, report in state_reports.items():
            # Find country for this state
            for state_data in self.states:
                if state_data['id'] == state_id:
                    country_id = state_data['country_id']
                    if country_id in country_reports:
                        report.parent_id = country_reports[country_id].id
                        report.save()
                    break