from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date
import calendar
from collections import defaultdict
from geographies.models.geos import Country, State, District, Subdistrict, Village
from users.models.petitioners import Petitioner
from reports.models.intitationreports import (
    VillageDailyReport, SubdistrictDailyReport, DistrictDailyReport,
    StateDailyReport, CountryDailyReport, CumulativeReport,
    VillageWeeklyReport, SubdistrictWeeklyReport, DistrictWeeklyReport,
    StateWeeklyReport, CountryWeeklyReport, VillageMonthlyReport,
    SubdistrictMonthlyReport, DistrictMonthlyReport, StateMonthlyReport,
    CountryMonthlyReport
)

class Command(BaseCommand):
    help = 'Backfill all historical reports from the first user registration date'

    def handle(self, *args, **kwargs):
        first_user = Petitioner.objects.order_by('date_joined').first()
        if not first_user:
            self.stdout.write("No users found. Exiting.")
            return

        start_date = first_user.date_joined.date()
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        self.stdout.write(f"Backfilling reports from {start_date} to {yesterday}")

        # Precompute geographical mappings once
        self.prepare_geographical_mappings()

        # Generate daily reports
        current_date = start_date
        while current_date <= yesterday:
            with transaction.atomic():
                self.generate_daily_reports_for_date(current_date)
            self.stdout.write(f"Generated daily report for {current_date}")
            current_date += timedelta(days=1)

        # Generate weekly reports
        self.stdout.write("Backfilling weekly reports...")
        self.backfill_weekly_reports(start_date, yesterday)

        # Generate monthly reports
        self.stdout.write("Backfilling monthly reports...")
        self.backfill_monthly_reports(start_date, yesterday)

        # Update cumulative reports
        with transaction.atomic():
            self.update_cumulative_reports()
        self.stdout.write("Updated cumulative reports")

        self.stdout.write("Backfill complete!")

    def prepare_geographical_mappings(self):
        """Precompute mappings between geographical entities for efficient lookups"""
        # Prefetch all geographical relationships
        villages = Village.objects.select_related(
            'subdistrict__district__state__country'
        ).all()
        
        self.village_mapping = {}
        self.subdistrict_mapping = defaultdict(list)
        self.district_mapping = defaultdict(list)
        self.state_mapping = defaultdict(list)
        self.country_mapping = defaultdict(list)
        
        for village in villages:
            self.village_mapping[village.id] = village
            if village.subdistrict:
                self.subdistrict_mapping[village.subdistrict_id].append(village)
                if village.subdistrict.district:
                    self.district_mapping[village.subdistrict.district_id].append(village.subdistrict)
                    if village.subdistrict.district.state:
                        self.state_mapping[village.subdistrict.district.state_id].append(village.subdistrict.district)
                        if village.subdistrict.district.state.country:
                            self.country_mapping[village.subdistrict.district.state.country_id].append(village.subdistrict.district.state)

    def generate_daily_reports_for_date(self, report_date):
        """Optimized daily report generation starting from petitioners"""
        # Get all users who joined on this date
        users = Petitioner.objects.filter(date_joined__date=report_date).select_related(
            'village', 'subdistrict', 'district', 'state', 'country'
        )
        
        # Group users by their geographical entities
        users_by_village = defaultdict(list)
        users_by_subdistrict = defaultdict(list)
        users_by_district = defaultdict(list)
        users_by_state = defaultdict(list)
        users_by_country = defaultdict(list)
        
        for user in users:
            if user.village_id:
                users_by_village[user.village_id].append(user)
            if user.subdistrict_id:
                users_by_subdistrict[user.subdistrict_id].append(user)
            if user.district_id:
                users_by_district[user.district_id].append(user)
            if user.state_id:
                users_by_state[user.state_id].append(user)
            if user.country_id:
                users_by_country[user.country_id].append(user)
        
        # Create village reports only for villages with users
        village_reports = {}
        for village_id, user_list in users_by_village.items():
            village = self.village_mapping.get(village_id)
            if village:
                user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in user_list}
                report = VillageDailyReport.objects.create(
                    village=village,
                    report_date=report_date,
                    new_users=len(user_list),
                    user_data=user_data
                )
                village_reports[village_id] = report
        
        # Create subdistrict reports for all subdistricts
        subdistrict_reports = {}
        for subdistrict_id in self.subdistrict_mapping.keys():
            user_list = users_by_subdistrict.get(subdistrict_id, [])
            villages_in_sub = self.subdistrict_mapping[subdistrict_id]
            
            village_data = {}
            total_users = 0
            
            # Aggregate data for villages in this subdistrict
            for village in villages_in_sub:
                count = 0
                report_id = None
                
                if village.id in village_reports:
                    report = village_reports[village.id]
                    count = report.new_users
                    report_id = report.id
                
                village_data[village.name] = {
                    "id": village.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create subdistrict report
            report = SubdistrictDailyReport.objects.create(
                subdistrict=village.subdistrict,  # All villages in sub share same subdistrict
                report_date=report_date,
                new_users=total_users,
                village_data=village_data
            )
            subdistrict_reports[subdistrict_id] = report
        
        # Create district reports for all districts
        district_reports = {}
        for district_id in self.district_mapping.keys():
            user_list = users_by_district.get(district_id, [])
            subdistricts_in_district = self.district_mapping[district_id]
            
            subdistrict_data = {}
            total_users = 0
            
            # Aggregate data for subdistricts in this district
            for subdistrict in subdistricts_in_district:
                count = 0
                report_id = None
                
                if subdistrict.id in subdistrict_reports:
                    report = subdistrict_reports[subdistrict.id]
                    count = report.new_users
                    report_id = report.id
                
                subdistrict_data[subdistrict.name] = {
                    "id": subdistrict.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create district report
            report = DistrictDailyReport.objects.create(
                district=subdistrict.district,  # All subdistricts share same district
                report_date=report_date,
                new_users=total_users,
                subdistrict_data=subdistrict_data
            )
            district_reports[district_id] = report
        
        # Create state reports for all states
        state_reports = {}
        for state_id in self.state_mapping.keys():
            user_list = users_by_state.get(state_id, [])
            districts_in_state = self.state_mapping[state_id]
            
            district_data = {}
            total_users = 0
            
            # Aggregate data for districts in this state
            for district in districts_in_state:
                count = 0
                report_id = None
                
                if district.id in district_reports:
                    report = district_reports[district.id]
                    count = report.new_users
                    report_id = report.id
                
                district_data[district.name] = {
                    "id": district.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create state report
            report = StateDailyReport.objects.create(
                state=district.state,  # All districts share same state
                report_date=report_date,
                new_users=total_users,
                district_data=district_data
            )
            state_reports[state_id] = report
        
        # Create country reports for all countries
        for country_id in self.country_mapping.keys():
            user_list = users_by_country.get(country_id, [])
            states_in_country = self.country_mapping[country_id]
            
            state_data = {}
            total_users = 0
            
            # Aggregate data for states in this country
            for state in states_in_country:
                count = 0
                report_id = None
                
                if state.id in state_reports:
                    report = state_reports[state.id]
                    count = report.new_users
                    report_id = report.id
                
                state_data[state.name] = {
                    "id": state.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create country report
            CountryDailyReport.objects.create(
                country=state.country,  # All states share same country
                report_date=report_date,
                new_users=total_users,
                state_data=state_data
            )

    def backfill_weekly_reports(self, start_date, end_date):
        """Generate weekly reports for all weeks between start_date and end_date"""
        # Get first Monday after start_date
        current_date = start_date
        while current_date.weekday() != 0:  # 0=Monday
            current_date += timedelta(days=1)
        
        while current_date <= end_date:
            week_end = current_date + timedelta(days=6)
            if week_end > end_date:
                break
                
            with transaction.atomic():
                self.generate_weekly_report_for_week(current_date, week_end)
            
            self.stdout.write(f"Generated weekly report for {current_date} to {week_end}")
            current_date += timedelta(weeks=1)

    def generate_weekly_report_for_week(self, start_date, end_date):
        """Optimized weekly report generation starting from petitioners"""
        week_number = end_date.isocalendar()[1]
        year = end_date.year
        
        # Get all users who joined during this week
        users = Petitioner.objects.filter(
            date_joined__date__range=(start_date, end_date)
        ).select_related(
            'village', 'subdistrict', 'district', 'state', 'country'
        )
        
        # Group users by their geographical entities
        users_by_village = defaultdict(list)
        users_by_subdistrict = defaultdict(list)
        users_by_district = defaultdict(list)
        users_by_state = defaultdict(list)
        users_by_country = defaultdict(list)
        
        for user in users:
            if user.village_id:
                users_by_village[user.village_id].append(user)
            if user.subdistrict_id:
                users_by_subdistrict[user.subdistrict_id].append(user)
            if user.district_id:
                users_by_district[user.district_id].append(user)
            if user.state_id:
                users_by_state[user.state_id].append(user)
            if user.country_id:
                users_by_country[user.country_id].append(user)
        
        # Create village reports only for villages with users
        village_reports = {}
        for village_id, user_list in users_by_village.items():
            village = self.village_mapping.get(village_id)
            if village:
                user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in user_list}
                report = VillageWeeklyReport.objects.create(
                    village=village,
                    report_date=end_date,
                    new_users=len(user_list),
                    user_data=user_data,
                    week_number=week_number,
                    year=year
                )
                village_reports[village_id] = report
        
        # Create subdistrict reports for all subdistricts
        subdistrict_reports = {}
        for subdistrict_id in self.subdistrict_mapping.keys():
            user_list = users_by_subdistrict.get(subdistrict_id, [])
            villages_in_sub = self.subdistrict_mapping[subdistrict_id]
            
            village_data = {}
            total_users = 0
            
            # Aggregate data for villages in this subdistrict
            for village in villages_in_sub:
                count = 0
                report_id = None
                
                if village.id in village_reports:
                    report = village_reports[village.id]
                    count = report.new_users
                    report_id = report.id
                
                village_data[village.name] = {
                    "id": village.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create subdistrict report
            report = SubdistrictWeeklyReport.objects.create(
                subdistrict=village.subdistrict,
                report_date=end_date,
                new_users=total_users,
                village_data=village_data,
                week_number=week_number,
                year=year
            )
            subdistrict_reports[subdistrict_id] = report
        
        # Create district reports for all districts
        district_reports = {}
        for district_id in self.district_mapping.keys():
            user_list = users_by_district.get(district_id, [])
            subdistricts_in_district = self.district_mapping[district_id]
            
            subdistrict_data = {}
            total_users = 0
            
            # Aggregate data for subdistricts in this district
            for subdistrict in subdistricts_in_district:
                count = 0
                report_id = None
                
                if subdistrict.id in subdistrict_reports:
                    report = subdistrict_reports[subdistrict.id]
                    count = report.new_users
                    report_id = report.id
                
                subdistrict_data[subdistrict.name] = {
                    "id": subdistrict.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create district report
            report = DistrictWeeklyReport.objects.create(
                district=subdistrict.district,
                report_date=end_date,
                new_users=total_users,
                subdistrict_data=subdistrict_data,
                week_number=week_number,
                year=year
            )
            district_reports[district_id] = report
        
        # Create state reports for all states
        state_reports = {}
        for state_id in self.state_mapping.keys():
            user_list = users_by_state.get(state_id, [])
            districts_in_state = self.state_mapping[state_id]
            
            district_data = {}
            total_users = 0
            
            # Aggregate data for districts in this state
            for district in districts_in_state:
                count = 0
                report_id = None
                
                if district.id in district_reports:
                    report = district_reports[district.id]
                    count = report.new_users
                    report_id = report.id
                
                district_data[district.name] = {
                    "id": district.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create state report
            report = StateWeeklyReport.objects.create(
                state=district.state,
                report_date=end_date,
                new_users=total_users,
                district_data=district_data,
                week_number=week_number,
                year=year
            )
            state_reports[state_id] = report
        
        # Create country reports for all countries
        for country_id in self.country_mapping.keys():
            user_list = users_by_country.get(country_id, [])
            states_in_country = self.country_mapping[country_id]
            
            state_data = {}
            total_users = 0
            
            # Aggregate data for states in this country
            for state in states_in_country:
                count = 0
                report_id = None
                
                if state.id in state_reports:
                    report = state_reports[state.id]
                    count = report.new_users
                    report_id = report.id
                
                state_data[state.name] = {
                    "id": state.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create country report
            CountryWeeklyReport.objects.create(
                country=state.country,
                report_date=end_date,
                new_users=total_users,
                state_data=state_data,
                week_number=week_number,
                year=year
            )

    def backfill_monthly_reports(self, start_date, end_date):
        """Generate monthly reports for all months between start_date and end_date"""
        current_date = start_date.replace(day=1)  # First day of month
        
        while current_date <= end_date:
            _, last_day = calendar.monthrange(current_date.year, current_date.month)
            month_end = date(current_date.year, current_date.month, last_day)
            
            if month_end > end_date:
                break
                
            with transaction.atomic():
                self.generate_monthly_report_for_month(current_date, month_end)
            
            self.stdout.write(f"Generated monthly report for {current_date.strftime('%Y-%m')}")
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year+1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month+1, day=1)

    def generate_monthly_report_for_month(self, start_date, end_date):
        """Optimized monthly report generation starting from petitioners"""
        month = end_date.month
        year = end_date.year
        
        # Get all users who joined during this month
        users = Petitioner.objects.filter(
            date_joined__date__range=(start_date, end_date)
        ).select_related(
            'village', 'subdistrict', 'district', 'state', 'country'
        )
        
        # Group users by their geographical entities
        users_by_village = defaultdict(list)
        users_by_subdistrict = defaultdict(list)
        users_by_district = defaultdict(list)
        users_by_state = defaultdict(list)
        users_by_country = defaultdict(list)
        
        for user in users:
            if user.village_id:
                users_by_village[user.village_id].append(user)
            if user.subdistrict_id:
                users_by_subdistrict[user.subdistrict_id].append(user)
            if user.district_id:
                users_by_district[user.district_id].append(user)
            if user.state_id:
                users_by_state[user.state_id].append(user)
            if user.country_id:
                users_by_country[user.country_id].append(user)
        
        # Create village reports only for villages with users
        village_reports = {}
        for village_id, user_list in users_by_village.items():
            village = self.village_mapping.get(village_id)
            if village:
                user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in user_list}
                report = VillageMonthlyReport.objects.create(
                    village=village,
                    report_date=end_date,
                    new_users=len(user_list),
                    user_data=user_data,
                    month=month,
                    year=year
                )
                village_reports[village_id] = report
        
        # Create subdistrict reports for all subdistricts
        subdistrict_reports = {}
        for subdistrict_id in self.subdistrict_mapping.keys():
            user_list = users_by_subdistrict.get(subdistrict_id, [])
            villages_in_sub = self.subdistrict_mapping[subdistrict_id]
            
            village_data = {}
            total_users = 0
            
            # Aggregate data for villages in this subdistrict
            for village in villages_in_sub:
                count = 0
                report_id = None
                
                if village.id in village_reports:
                    report = village_reports[village.id]
                    count = report.new_users
                    report_id = report.id
                
                village_data[village.name] = {
                    "id": village.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create subdistrict report
            report = SubdistrictMonthlyReport.objects.create(
                subdistrict=village.subdistrict,
                report_date=end_date,
                new_users=total_users,
                village_data=village_data,
                month=month,
                year=year
            )
            subdistrict_reports[subdistrict_id] = report
        
        # Create district reports for all districts
        district_reports = {}
        for district_id in self.district_mapping.keys():
            user_list = users_by_district.get(district_id, [])
            subdistricts_in_district = self.district_mapping[district_id]
            
            subdistrict_data = {}
            total_users = 0
            
            # Aggregate data for subdistricts in this district
            for subdistrict in subdistricts_in_district:
                count = 0
                report_id = None
                
                if subdistrict.id in subdistrict_reports:
                    report = subdistrict_reports[subdistrict.id]
                    count = report.new_users
                    report_id = report.id
                
                subdistrict_data[subdistrict.name] = {
                    "id": subdistrict.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create district report
            report = DistrictMonthlyReport.objects.create(
                district=subdistrict.district,
                report_date=end_date,
                new_users=total_users,
                subdistrict_data=subdistrict_data,
                month=month,
                year=year
            )
            district_reports[district_id] = report
        
        # Create state reports for all states
        state_reports = {}
        for state_id in self.state_mapping.keys():
            user_list = users_by_state.get(state_id, [])
            districts_in_state = self.state_mapping[state_id]
            
            district_data = {}
            total_users = 0
            
            # Aggregate data for districts in this state
            for district in districts_in_state:
                count = 0
                report_id = None
                
                if district.id in district_reports:
                    report = district_reports[district.id]
                    count = report.new_users
                    report_id = report.id
                
                district_data[district.name] = {
                    "id": district.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create state report
            report = StateMonthlyReport.objects.create(
                state=district.state,
                report_date=end_date,
                new_users=total_users,
                district_data=district_data,
                month=month,
                year=year
            )
            state_reports[state_id] = report
        
        # Create country reports for all countries
        for country_id in self.country_mapping.keys():
            user_list = users_by_country.get(country_id, [])
            states_in_country = self.country_mapping[country_id]
            
            state_data = {}
            total_users = 0
            
            # Aggregate data for states in this country
            for state in states_in_country:
                count = 0
                report_id = None
                
                if state.id in state_reports:
                    report = state_reports[state.id]
                    count = report.new_users
                    report_id = report.id
                
                state_data[state.name] = {
                    "id": state.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            # Create country report
            CountryMonthlyReport.objects.create(
                country=state.country,
                report_date=end_date,
                new_users=total_users,
                state_data=state_data,
                month=month,
                year=year
            )

    def update_cumulative_reports(self):
        """Optimized cumulative report generation"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Get all users who have ever joined
        all_users = Petitioner.objects.all().select_related(
            'village', 'subdistrict', 'district', 'state', 'country'
        )
        
        # Group users by their geographical entities
        users_by_village = defaultdict(list)
        users_by_subdistrict = defaultdict(list)
        users_by_district = defaultdict(list)
        users_by_state = defaultdict(list)
        users_by_country = defaultdict(list)
        
        for user in all_users:
            if user.village_id:
                users_by_village[user.village_id].append(user)
            if user.subdistrict_id:
                users_by_subdistrict[user.subdistrict_id].append(user)
            if user.district_id:
                users_by_district[user.district_id].append(user)
            if user.state_id:
                users_by_state[user.state_id].append(user)
            if user.country_id:
                users_by_country[user.country_id].append(user)
        
        # Create village cumulative reports
        village_reports = {}
        for village_id, user_list in users_by_village.items():
            village = self.village_mapping.get(village_id)
            if village:
                user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in user_list}
                report = CumulativeReport.objects.create(
                    level='village',
                    village=village,
                    report_date=yesterday,
                    total_users=len(user_list),
                    user_data=user_data
                )
                village_reports[village_id] = report
        
        # Create subdistrict cumulative reports
        subdistrict_reports = {}
        for subdistrict_id in self.subdistrict_mapping.keys():
            user_list = users_by_subdistrict.get(subdistrict_id, [])
            villages_in_sub = self.subdistrict_mapping[subdistrict_id]
            
            village_data = {}
            total_users = 0
            
            for village in villages_in_sub:
                count = 0
                report_id = None
                
                if village.id in village_reports:
                    report = village_reports[village.id]
                    count = report.total_users
                    report_id = report.id
                
                village_data[village.name] = {
                    "id": village.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            report = CumulativeReport.objects.create(
                level='subdistrict',
                subdistrict=village.subdistrict,
                report_date=yesterday,
                total_users=total_users,
                user_data=village_data
            )
            subdistrict_reports[subdistrict_id] = report
        
        # Create district cumulative reports
        district_reports = {}
        for district_id in self.district_mapping.keys():
            user_list = users_by_district.get(district_id, [])
            subdistricts_in_district = self.district_mapping[district_id]
            
            subdistrict_data = {}
            total_users = 0
            
            for subdistrict in subdistricts_in_district:
                count = 0
                report_id = None
                
                if subdistrict.id in subdistrict_reports:
                    report = subdistrict_reports[subdistrict.id]
                    count = report.total_users
                    report_id = report.id
                
                subdistrict_data[subdistrict.name] = {
                    "id": subdistrict.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            report = CumulativeReport.objects.create(
                level='district',
                district=subdistrict.district,
                report_date=yesterday,
                total_users=total_users,
                user_data=subdistrict_data
            )
            district_reports[district_id] = report
        
        # Create state cumulative reports
        state_reports = {}
        for state_id in self.state_mapping.keys():
            user_list = users_by_state.get(state_id, [])
            districts_in_state = self.state_mapping[state_id]
            
            district_data = {}
            total_users = 0
            
            for district in districts_in_state:
                count = 0
                report_id = None
                
                if district.id in district_reports:
                    report = district_reports[district.id]
                    count = report.total_users
                    report_id = report.id
                
                district_data[district.name] = {
                    "id": district.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            report = CumulativeReport.objects.create(
                level='state',
                state=district.state,
                report_date=yesterday,
                total_users=total_users,
                user_data=district_data
            )
            state_reports[state_id] = report
        
        # Create country cumulative reports
        for country_id in self.country_mapping.keys():
            user_list = users_by_country.get(country_id, [])
            states_in_country = self.country_mapping[country_id]
            
            state_data = {}
            total_users = 0
            
            for state in states_in_country:
                count = 0
                report_id = None
                
                if state.id in state_reports:
                    report = state_reports[state.id]
                    count = report.total_users
                    report_id = report.id
                
                state_data[state.name] = {
                    "id": state.id,
                    "count": count,
                    "report_id": report_id
                }
                total_users += count
            
            CumulativeReport.objects.create(
                level='country',
                country=state.country,
                report_date=yesterday,
                total_users=total_users,
                user_data=state_data
            )