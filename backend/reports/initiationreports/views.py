from django.db import transaction
from django.utils import timezone
from datetime import timedelta, datetime, date
from collections import defaultdict
import calendar
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

def generate_daily_reports():
    today = timezone.now().date()
    report_date = today - timedelta(days=1)  # Yesterday's report
    
    # 1. Generate village reports only for villages with new users
    village_reports = {}
    all_villages = Village.objects.all().prefetch_related('subdistrict')
    
    for village in all_villages:
        users = Petitioner.objects.filter(
            village=village,
            date_joined__date=report_date
        )
        if users.exists():
            user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in users}
            report = VillageDailyReport.objects.create(
                village=village,
                report_date=report_date,
                new_users=users.count(),
                user_data=user_data
            )
            village_reports[village.id] = report
    
    # 2. Generate subdistrict reports for ALL subdistricts
    subdistrict_reports = {}
    all_subdistricts = Subdistrict.objects.all().prefetch_related('villages', 'district')
    
    for subdistrict in all_subdistricts:
        villages = subdistrict.villages.all()
        village_data = {}
        total_users = 0
        
        for village in villages:
            report = village_reports.get(village.id)
            count = report.new_users if report else 0
            total_users += count
            
            village_data[village.name] = {
                "id": village.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = SubdistrictDailyReport.objects.create(
            subdistrict=subdistrict,
            report_date=report_date,
            new_users=total_users,
            village_data=village_data
        )
        subdistrict_reports[subdistrict.id] = report
    
    # 3. Generate district reports for ALL districts
    district_reports = {}
    all_districts = District.objects.all().prefetch_related('subdistricts', 'state')
    
    for district in all_districts:
        subdistricts = district.subdistricts.all()
        subdistrict_data = {}
        total_users = 0
        
        for sub in subdistricts:
            report = subdistrict_reports.get(sub.id)
            count = report.new_users if report else 0
            total_users += count
            
            subdistrict_data[sub.name] = {
                "id": sub.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = DistrictDailyReport.objects.create(
            district=district,
            report_date=report_date,
            new_users=total_users,
            subdistrict_data=subdistrict_data
        )
        district_reports[district.id] = report
    
    # 4. Generate state reports for ALL states
    state_reports = {}
    all_states = State.objects.all().prefetch_related('districts', 'country')
    
    for state in all_states:
        districts = state.districts.all()
        district_data = {}
        total_users = 0
        
        for district in districts:
            report = district_reports.get(district.id)
            count = report.new_users if report else 0
            total_users += count
            
            district_data[district.name] = {
                "id": district.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = StateDailyReport.objects.create(
            state=state,
            report_date=report_date,
            new_users=total_users,
            district_data=district_data
        )
        state_reports[state.id] = report
    
    # 5. Generate country reports for ALL countries
    all_countries = Country.objects.all().prefetch_related('states')
    
    for country in all_countries:
        states = country.states.all()
        state_data = {}
        total_users = 0
        
        for state in states:
            report = state_reports.get(state.id)
            count = report.new_users if report else 0
            total_users += count
            
            state_data[state.name] = {
                "id": state.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        CountryDailyReport.objects.create(
            country=country,
            report_date=report_date,
            new_users=total_users,
            state_data=state_data
        )

def generate_weekly_reports():
    today = timezone.now().date()
    week_number = today.isocalendar()[1]
    year = today.year
    start_date = today - timedelta(days=today.weekday() + 7)  # Start of previous week
    end_date = start_date + timedelta(days=6)  # End of previous week
    
    # 1. Generate village reports only for villages with weekly users
    village_reports = {}
    all_villages = Village.objects.all().prefetch_related('subdistrict')
    
    for village in all_villages:
        users = Petitioner.objects.filter(
            village=village,
            date_joined__date__range=(start_date, end_date)
        )
        if users.exists():
            user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in users}
            report = VillageWeeklyReport.objects.create(
                village=village,
                report_date=end_date,
                new_users=users.count(),
                user_data=user_data,
                week_number=week_number,
                year=year
            )
            village_reports[village.id] = report
    
    # 2. Generate subdistrict reports for ALL subdistricts
    subdistrict_reports = {}
    all_subdistricts = Subdistrict.objects.all().prefetch_related('villages', 'district')
    
    for subdistrict in all_subdistricts:
        villages = subdistrict.villages.all()
        village_data = {}
        total_users = 0
        
        for village in villages:
            report = village_reports.get(village.id)
            count = report.new_users if report else 0
            total_users += count
            
            village_data[village.name] = {
                "id": village.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = SubdistrictWeeklyReport.objects.create(
            subdistrict=subdistrict,
            report_date=end_date,
            new_users=total_users,
            village_data=village_data,
            week_number=week_number,
            year=year
        )
        subdistrict_reports[subdistrict.id] = report
    
    # 3. Generate district reports for ALL districts
    district_reports = {}
    all_districts = District.objects.all().prefetch_related('subdistricts', 'state')
    
    for district in all_districts:
        subdistricts = district.subdistricts.all()
        subdistrict_data = {}
        total_users = 0
        
        for sub in subdistricts:
            report = subdistrict_reports.get(sub.id)
            count = report.new_users if report else 0
            total_users += count
            
            subdistrict_data[sub.name] = {
                "id": sub.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = DistrictWeeklyReport.objects.create(
            district=district,
            report_date=end_date,
            new_users=total_users,
            subdistrict_data=subdistrict_data,
            week_number=week_number,
            year=year
        )
        district_reports[district.id] = report

    # 4. Generate state reports for ALL states
    state_reports = {}
    all_states = State.objects.all().prefetch_related('districts', 'country')
    
    for state in all_states:
        districts = state.districts.all()
        district_data = {}
        total_users = 0
        
        for district in districts:
            report = district_reports.get(district.id)
            count = report.new_users if report else 0
            total_users += count
            
            district_data[district.name] = {
                "id": district.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = StateWeeklyReport.objects.create(
            state=state,
            report_date=end_date,
            new_users=total_users,
            district_data=district_data,
            week_number=week_number,
            year=year
        )
        state_reports[state.id] = report

    # 5. Generate country reports for ALL countries
    all_countries = Country.objects.all().prefetch_related('states')
    
    for country in all_countries:
        states = country.states.all()
        state_data = {}
        total_users = 0
        
        for state in states:
            report = state_reports.get(state.id)
            count = report.new_users if report else 0
            total_users += count
            
            state_data[state.name] = {
                "id": state.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        CountryWeeklyReport.objects.create(
            country=country,
            report_date=end_date,
            new_users=total_users,
            state_data=state_data,
            week_number=week_number,
            year=year
        )


def generate_monthly_reports():
    today = timezone.now().date()
    month = today.month
    year = today.year
    
    # Calculate previous month
    if today.month == 1:
        prev_month = 12
        prev_year = today.year - 1
    else:
        prev_month = today.month - 1
        prev_year = today.year
    
    # Get first and last day of previous month
    _, last_day = calendar.monthrange(prev_year, prev_month)
    start_date = date(prev_year, prev_month, 1)
    end_date = date(prev_year, prev_month, last_day)
    
    # 1. Generate village reports only for villages with monthly users
    village_reports = {}
    all_villages = Village.objects.all().prefetch_related('subdistrict')
    
    for village in all_villages:
        users = Petitioner.objects.filter(
            village=village,
            date_joined__date__range=(start_date, end_date)
        )
        if users.exists():
            user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in users}
            report = VillageMonthlyReport.objects.create(
                village=village,
                report_date=end_date,
                new_users=users.count(),
                user_data=user_data,
                month=prev_month,
                year=prev_year
            )
            village_reports[village.id] = report
    
    # 2. Generate subdistrict reports for ALL subdistricts
    subdistrict_reports = {}
    all_subdistricts = Subdistrict.objects.all().prefetch_related('villages', 'district')
    
    for subdistrict in all_subdistricts:
        villages = subdistrict.villages.all()
        village_data = {}
        total_users = 0
        
        for village in villages:
            report = village_reports.get(village.id)
            count = report.new_users if report else 0
            total_users += count
            
            village_data[village.name] = {
                "id": village.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = SubdistrictMonthlyReport.objects.create(
            subdistrict=subdistrict,
            report_date=end_date,
            new_users=total_users,
            village_data=village_data,
            month=prev_month,
            year=prev_year
        )
        subdistrict_reports[subdistrict.id] = report
    
    # 3. Generate district reports for ALL districts
    district_reports = {}
    all_districts = District.objects.all().prefetch_related('subdistricts', 'state')
    
    for district in all_districts:
        subdistricts = district.subdistricts.all()
        subdistrict_data = {}
        total_users = 0
        
        for sub in subdistricts:
            report = subdistrict_reports.get(sub.id)
            count = report.new_users if report else 0
            total_users += count
            
            subdistrict_data[sub.name] = {
                "id": sub.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = DistrictMonthlyReport.objects.create(
            district=district,
            report_date=end_date,
            new_users=total_users,
            subdistrict_data=subdistrict_data,
            month=prev_month,
            year=prev_year
        )
        district_reports[district.id] = report

    # 4. Generate state reports for ALL states
    state_reports = {}
    all_states = State.objects.all().prefetch_related('districts', 'country')
    
    for state in all_states:
        districts = state.districts.all()
        district_data = {}
        total_users = 0
        
        for district in districts:
            report = district_reports.get(district.id)
            count = report.new_users if report else 0
            total_users += count
            
            district_data[district.name] = {
                "id": district.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        report = StateMonthlyReport.objects.create(
            state=state,
            report_date=end_date,
            new_users=total_users,
            district_data=district_data,
            month=prev_month,
            year=prev_year
        )
        state_reports[state.id] = report

    # 5. Generate country reports for ALL countries
    all_countries = Country.objects.all().prefetch_related('states')
    
    for country in all_countries:
        states = country.states.all()
        state_data = {}
        total_users = 0
        
        for state in states:
            report = state_reports.get(state.id)
            count = report.new_users if report else 0
            total_users += count
            
            state_data[state.name] = {
                "id": state.id,
                "count": count,
                "report_id": report.id if report else None
            }
        
        CountryMonthlyReport.objects.create(
            country=country,
            report_date=end_date,
            new_users=total_users,
            state_data=state_data,
            month=prev_month,
            year=prev_year
        )


def update_cumulative_reports():
    # Village cumulative reports (only create for villages with users)
    villages_with_users = Village.objects.filter(
        petitioner__isnull=False
    ).distinct().prefetch_related('petitioner_set')
    
    for village in villages_with_users:
        users = village.petitioner_set.all()
        user_data = {str(u.id): f"{u.first_name} {u.last_name}" for u in users}
        
        CumulativeReport.objects.update_or_create(
            level='village',
            geographical_entity=village.id,
            defaults={
                'total_users': users.count(),
                'user_data': user_data
            }
        )
    
    # Remove cumulative reports for villages with no users
    CumulativeReport.objects.filter(
        level='village'
    ).exclude(
        geographical_entity__in=[v.id for v in villages_with_users]
    ).delete()
    
    # Subdistrict cumulative reports (create for ALL subdistricts)
    all_subdistricts = Subdistrict.objects.all().prefetch_related('villages')
    
    for sub in all_subdistricts:
        total = Petitioner.objects.filter(village__subdistrict=sub).count()
        CumulativeReport.objects.update_or_create(
            level='subdistrict',
            geographical_entity=sub.id,
            defaults={'total_users': total}
        )
    
    # District cumulative reports (create for ALL districts)
    all_districts = District.objects.all().prefetch_related('subdistricts')
    
    for district in all_districts:
        total = Petitioner.objects.filter(village__subdistrict__district=district).count()
        CumulativeReport.objects.update_or_create(
            level='district',
            geographical_entity=district.id,
            defaults={'total_users': total}
        )
    
    # State cumulative reports (create for ALL states)
    all_states = State.objects.all().prefetch_related('districts')
    
    for state in all_states:
        total = Petitioner.objects.filter(village__subdistrict__district__state=state).count()
        CumulativeReport.objects.update_or_create(
            level='state',
            geographical_entity=state.id,
            defaults={'total_users': total}
        )
    
    # Country cumulative reports (create for ALL countries)
    all_countries = Country.objects.all().prefetch_related('states')
    
    for country in all_countries:
        total = Petitioner.objects.filter(country=country).count()
        CumulativeReport.objects.update_or_create(
            level='country',
            geographical_entity=country.id,
            defaults={'total_users': total}
        )