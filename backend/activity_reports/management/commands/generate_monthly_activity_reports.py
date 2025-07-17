# activity_reports/management/commands/generate_monthly_activity_reports.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from collections import defaultdict
import calendar
from geographies.models.geos import Village, Subdistrict, District, State, Country
from activity_reports.models import (
    DailyActivitySummary,
    MonthlyVillageActivityReport,
    MonthlySubdistrictActivityReport,
    MonthlyDistrictActivityReport,
    MonthlyStateActivityReport,
    MonthlyCountryActivityReport
)
from users.models import Petitioner

class Command(BaseCommand):
    help = 'Generates monthly activity reports for all geographic levels'
    
    # Define our activity buckets (in days)
    ACTIVITY_BUCKETS = [1, 5, 10, 15, 20, 25, 30]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: first activity date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: last month)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing reports'
        )
    
    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        force = kwargs['force']
        
        self.stdout.write(f"Generating monthly reports from {start_date} to {end_date}")
        if force:
            self.stdout.write("Force mode: Replacing existing reports")
        
        # Preload geographic hierarchy
        self.preload_geographic_data()
        
        current_date = start_date
        processed_months = 0
        
        while current_date <= end_date:
            # Get first and last day of month
            first_day = date(current_date.year, current_date.month, 1)
            last_day = date(
                current_date.year, 
                current_date.month, 
                calendar.monthrange(current_date.year, current_date.month)[1]
            )
            
            self.stdout.write(f"\nProcessing {first_day.strftime('%B %Y')} "
                             f"({first_day} to {last_day})")
            
            with transaction.atomic():
                # Delete existing reports if forcing regeneration
                if force:
                    self.delete_existing_monthly_reports(current_date.month, current_date.year)
                
                # Get all active users in this month
                monthly_activity = self.get_monthly_activity(first_day, last_day)
                
                if not monthly_activity:
                    self.stdout.write(f"No activity data for {first_day.strftime('%B %Y')}, skipping")
                    current_date = self.next_month(current_date)
                    continue
                
                # Create reports bottom-up
                village_reports = self.create_village_reports(
                    first_day, last_day, current_date.month, current_date.year, monthly_activity
                )
                subdistrict_reports = self.create_subdistrict_reports(
                    first_day, last_day, current_date.month, current_date.year, village_reports, monthly_activity
                )
                district_reports = self.create_district_reports(
                    first_day, last_day, current_date.month, current_date.year, subdistrict_reports, monthly_activity
                )
                state_reports = self.create_state_reports(
                    first_day, last_day, current_date.month, current_date.year, district_reports, monthly_activity
                )
                country_reports = self.create_country_reports(
                    first_day, last_day, current_date.month, current_date.year, state_reports, monthly_activity
                )
                
                # Set parent IDs after creating all reports
                self.set_parent_ids(
                    village_reports, 
                    subdistrict_reports, 
                    district_reports, 
                    state_reports, 
                    country_reports
                )
            
            current_date = self.next_month(current_date)
            processed_months += 1
            
            if processed_months % 3 == 0:
                self.stdout.write(f"Processed {processed_months} months...")
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated monthly activity reports for {processed_months} months'
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
        
        # Preload user names and locations
        self.user_info = {}
        for user in Petitioner.objects.only('id', 'first_name', 'last_name', 'village_id', 'subdistrict_id', 'district_id', 'state_id', 'country_id'):
            self.user_info[user.id] = {
                'name': f"{user.first_name} {user.last_name}",
                'village_id': user.village_id,
                'subdistrict_id': user.subdistrict_id,
                'district_id': user.district_id,
                'state_id': user.state_id,
                'country_id': user.country_id
            }
    
    def next_month(self, dt):
        """Get first day of next month"""
        if dt.month == 12:
            return date(dt.year + 1, 1, 1)
        return date(dt.year, dt.month + 1, 1)
    
    def delete_existing_monthly_reports(self, month, year):
        """Delete existing monthly reports for a specific month"""
        MonthlyVillageActivityReport.objects.filter(
            month=month, year=year
        ).delete()
        MonthlySubdistrictActivityReport.objects.filter(
            month=month, year=year
        ).delete()
        MonthlyDistrictActivityReport.objects.filter(
            month=month, year=year
        ).delete()
        MonthlyStateActivityReport.objects.filter(
            month=month, year=year
        ).delete()
        MonthlyCountryActivityReport.objects.filter(
            month=month, year=year
        ).delete()
    
    def get_date_range(self, kwargs):
        """Determine the date range for report generation"""
        first_activity = DailyActivitySummary.objects.order_by('date').first()
        if not first_activity:
            raise ValueError("No activity data found in database")
        
        # Start from first day of month containing first activity
        default_start = first_activity.date.replace(day=1)
        
        # End at last month (completed months)
        today = date.today()
        if today.month == 1:
            default_end = date(today.year - 1, 12, 1)
        else:
            default_end = date(today.year, today.month - 1, 1)
        
        if default_end < default_start:
            default_end = default_start
        
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
        
        # Ensure dates are first of month
        start_date = start_date.replace(day=1)
        end_date = end_date.replace(day=1)
        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date >= date.today().replace(day=1):
            raise ValueError("End date must be in the past")
        
        return start_date, end_date
    
    def get_monthly_activity(self, month_start, month_end):
        """Get all user activity for a month with frequency counts"""
        # Get all daily summaries in the month
        daily_summaries = DailyActivitySummary.objects.filter(
            date__gte=month_start,
            date__lte=month_end
        ).order_by('date')
        
        if not daily_summaries:
            return None
        
        # Track user activity frequency
        user_activity = defaultdict(int)
        
        for summary in daily_summaries:
            for user_id in summary.active_users:
                user_activity[user_id] += 1
        
        return user_activity
    
    def calculate_activity_distribution(self, frequencies):
        """Calculate activity distribution for custom buckets"""
        distribution = {str(bucket): 0 for bucket in self.ACTIVITY_BUCKETS}
        
        for freq in frequencies:
            # For each bucket, if user meets or exceeds the threshold, count them
            for bucket in self.ACTIVITY_BUCKETS:
                if freq >= bucket:
                    distribution[str(bucket)] += 1
        
        return distribution
    
    def create_village_reports(self, month_start, month_end, month, year, monthly_activity):
        """Create village reports only for villages with active users"""
        village_users = defaultdict(lambda: defaultdict(int))
        village_reports = {}
        
        # Group active users by village
        for user_id, frequency in monthly_activity.items():
            user_info = self.user_info.get(user_id)
            if user_info and user_info['village_id']:
                village_id = user_info['village_id']
                village_users[village_id][user_id] = frequency
        
        # Create reports only for villages with activity
        for village_id, users in village_users.items():
            # Calculate activity distribution
            distribution = self.calculate_activity_distribution(users.values())
            user_data = {}
            
            for user_id, frequency in users.items():
                user_data[str(user_id)] = {
                    "id": user_id,
                    "name": self.user_info[user_id]['name'],
                    "active_days": frequency
                }
            
            # Create report
            report = MonthlyVillageActivityReport.objects.create(
                village_id=village_id,
                active_users=len(users),
                month=month,
                year=year,
                last_date=month_end,
                user_data=user_data,
                additional_info={"activity_distribution": distribution}
            )
            village_reports[village_id] = report
        
        return village_reports
    
    def create_subdistrict_reports(self, month_start, month_end, month, year, village_reports, monthly_activity):
        """Create subdistrict reports only for subdistricts with active users"""
        # Track active users per subdistrict
        subdistrict_activity = defaultdict(int)
        subdistrict_users = defaultdict(lambda: defaultdict(int))
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
        
        # Group users by subdistrict
        for user_id, frequency in monthly_activity.items():
            user_info = self.user_info.get(user_id)
            if user_info and user_info['subdistrict_id']:
                subdistrict_id = user_info['subdistrict_id']
                subdistrict_users[subdistrict_id][user_id] = frequency
        
        # Create reports only for subdistricts with activity
        subdistrict_reports = {}
        for subdistrict_id, active_count in subdistrict_activity.items():
            if active_count > 0:
                # Calculate distribution from actual user activity
                users = subdistrict_users.get(subdistrict_id, {})
                distribution = self.calculate_activity_distribution(users.values())
                
                report = MonthlySubdistrictActivityReport.objects.create(
                    subdistrict_id=subdistrict_id,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    village_data=subdistrict_village_reports[subdistrict_id],
                    additional_info={"activity_distribution": distribution}
                )
                subdistrict_reports[subdistrict_id] = report
        
        return subdistrict_reports
    
    def create_district_reports(self, month_start, month_end, month, year, subdistrict_reports, monthly_activity):
        """Create district reports only for districts with active users"""
        # Track activity per district
        district_activity = defaultdict(int)
        district_users = defaultdict(lambda: defaultdict(int))
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
        
        # Group users by district
        for user_id, frequency in monthly_activity.items():
            user_info = self.user_info.get(user_id)
            if user_info and user_info['district_id']:
                district_id = user_info['district_id']
                district_users[district_id][user_id] = frequency
        
        # Create reports only for districts with activity
        district_reports = {}
        for district_id, active_count in district_activity.items():
            if active_count > 0:
                # Calculate distribution from actual user activity
                users = district_users.get(district_id, {})
                distribution = self.calculate_activity_distribution(users.values())
                
                report = MonthlyDistrictActivityReport.objects.create(
                    district_id=district_id,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    subdistrict_data=district_subdistrict_reports[district_id],
                    additional_info={"activity_distribution": distribution}
                )
                district_reports[district_id] = report
        
        return district_reports
    
    def create_state_reports(self, month_start, month_end, month, year, district_reports, monthly_activity):
        """Create state reports only for states with active users"""
        # Track activity per state
        state_activity = defaultdict(int)
        state_users = defaultdict(lambda: defaultdict(int))
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
        
        # Group users by state
        for user_id, frequency in monthly_activity.items():
            user_info = self.user_info.get(user_id)
            if user_info and user_info['state_id']:
                state_id = user_info['state_id']
                state_users[state_id][user_id] = frequency
        
        # Create reports only for states with activity
        state_reports = {}
        for state_id, active_count in state_activity.items():
            if active_count > 0:
                # Calculate distribution from actual user activity
                users = state_users.get(state_id, {})
                distribution = self.calculate_activity_distribution(users.values())
                
                report = MonthlyStateActivityReport.objects.create(
                    state_id=state_id,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    district_data=state_district_reports[state_id],
                    additional_info={"activity_distribution": distribution}
                )
                state_reports[state_id] = report
        
        return state_reports
    
    def create_country_reports(self, month_start, month_end, month, year, state_reports, monthly_activity):
        """Create country reports only for countries with active users"""
        # Track activity per country
        country_activity = defaultdict(int)
        country_users = defaultdict(lambda: defaultdict(int))
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
        
        # Group users by country
        for user_id, frequency in monthly_activity.items():
            user_info = self.user_info.get(user_id)
            if user_info and user_info['country_id']:
                country_id = user_info['country_id']
                country_users[country_id][user_id] = frequency
        
        # Create reports only for countries with activity
        country_reports = {}
        for country_id, active_count in country_activity.items():
            if active_count > 0:
                # Calculate distribution from actual user activity
                users = country_users.get(country_id, {})
                distribution = self.calculate_activity_distribution(users.values())
                
                report = MonthlyCountryActivityReport.objects.create(
                    country_id=country_id,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    state_data=country_state_reports[country_id],
                    additional_info={"activity_distribution": distribution}
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