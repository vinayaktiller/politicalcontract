from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import (
    VillageWeeklyReport, SubdistrictWeeklyReport,
    DistrictWeeklyReport, StateWeeklyReport, CountryWeeklyReport,
    VillageDailyReport
)
from users.models.petitioners import Petitioner
from collections import defaultdict

class Command(BaseCommand):
    help = 'Generates weekly reports for all geographic levels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: first user week start)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: last full week)'
        )

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        self.stdout.write(f"Generating weekly reports from {start_date} to {end_date}")

        current_week_start = start_date
        processed_weeks = 0

        while current_week_start <= end_date:
            week_number = current_week_start.isocalendar()[1]
            year = current_week_start.isocalendar()[0]
            week_end = current_week_start + timedelta(days=6)

            self.stdout.write(
                f"Processing Week {week_number} ({current_week_start} to {week_end})..."
            )

            with transaction.atomic():
                village_reports = self.create_village_weekly_reports(
                    current_week_start, week_end, week_number, year
                )
                subdistrict_reports = self.create_subdistrict_weekly_reports(
                    week_number, year, current_week_start, week_end, village_reports
                )
                district_reports = self.create_district_weekly_reports(
                    week_number, year, current_week_start, week_end, subdistrict_reports
                )
                state_reports = self.create_state_weekly_reports(
                    week_number, year, current_week_start, week_end, district_reports
                )
                # Ensure country report is ALWAYS created, even with zero total_users
                country_reports = self.create_country_weekly_reports(
                    week_number, year, current_week_start, week_end, state_reports
                )
                self.update_parent_ids(
                    village_reports,
                    subdistrict_reports,
                    district_reports,
                    state_reports,
                    country_reports
                )

            current_week_start += timedelta(days=7)
            processed_weeks += 1

            if processed_weeks % 4 == 0:
                self.stdout.write(f"Processed {processed_weeks} weeks...")

        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated weekly reports for {processed_weeks} weeks'
        ))

    def get_date_range(self, kwargs):
        # Earliest week from first user
        first_user = Petitioner.objects.order_by('date_joined').first()
        if not first_user:
            self.stdout.write(self.style.WARNING('No users found. Exiting.'))
            exit(0)

        first_date = first_user.date_joined.date()
        default_start = first_date - timedelta(days=first_date.weekday())  # Monday

        # Default end date is last full week start
        today = date.today()
        last_monday = today - timedelta(days=today.weekday() + 7)
        default_end = last_monday

        start_date = (
            self.get_week_start(date.fromisoformat(kwargs['start_date']))
            if kwargs.get('start_date')
            else default_start
        )
        end_date = (
            self.get_week_start(date.fromisoformat(kwargs['end_date']))
            if kwargs.get('end_date')
            else default_end
        )

        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")

        return start_date, end_date

    def get_week_start(self, dt):
        """Get the Monday of the week containing the given date"""
        return dt - timedelta(days=dt.weekday())

    def create_village_weekly_reports(self, week_start, week_end, week_number, year):
        daily_reports = VillageDailyReport.objects.filter(
            date__range=[week_start, week_end]
        ).select_related('village')

        village_data = defaultdict(lambda: {'users': 0, 'user_data': {}})

        for report in daily_reports:
            village_id = report.village_id
            village_data[village_id]['users'] += report.new_users
            village_data[village_id]['user_data'].update(report.user_data)

        reports_created = {}
        for village_id, data in village_data.items():
            if data['users'] == 0:
                continue

            village = Village.objects.get(id=village_id)
            report, created = VillageWeeklyReport.objects.update_or_create(
                week_last_date=week_end,
                village=village,
                week_number=week_number,
                year=year,
                defaults={
                    'week_start_date': week_start,
                    'new_users': data['users'],
                    'user_data': data['user_data'],
                    'parent_id': None
                }
            )
            reports_created[village_id] = report

        # Delete zero-user reports
        VillageWeeklyReport.objects.filter(
            week_last_date=week_end,
            new_users=0
        ).delete()

        return reports_created

    def create_subdistrict_weekly_reports(self, week_number, year, week_start, week_end, village_reports):
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
                # Remove if zero
                SubdistrictWeeklyReport.objects.filter(
                    week_last_date=week_end,
                    subdistrict=subdistrict
                ).delete()
                continue

            report, created = SubdistrictWeeklyReport.objects.update_or_create(
                week_last_date=week_end,
                subdistrict=subdistrict,
                week_number=week_number,
                year=year,
                defaults={
                    'week_start_date': week_start,
                    'new_users': total_users,
                    'village_data': village_data,
                    'parent_id': None
                }
            )
            reports_created[subdistrict_id] = report

        return reports_created

    def create_district_weekly_reports(self, week_number, year, week_start, week_end, subdistrict_reports):
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
                # Remove if zero
                DistrictWeeklyReport.objects.filter(
                    week_last_date=week_end,
                    district=district
                ).delete()
                continue

            report, created = DistrictWeeklyReport.objects.update_or_create(
                week_last_date=week_end,
                district=district,
                week_number=week_number,
                year=year,
                defaults={
                    'week_start_date': week_start,
                    'new_users': total_users,
                    'subdistrict_data': subdistrict_data,
                    'parent_id': None
                }
            )
            reports_created[district_id] = report

        return reports_created

    def create_state_weekly_reports(self, week_number, year, week_start, week_end, district_reports):
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
                # Remove if zero
                StateWeeklyReport.objects.filter(
                    week_last_date=week_end,
                    state=state
                ).delete()
                continue

            report, created = StateWeeklyReport.objects.update_or_create(
                week_last_date=week_end,
                state=state,
                week_number=week_number,
                year=year,
                defaults={
                    'week_start_date': week_start,
                    'new_users': total_users,
                    'district_data': district_data,
                    'parent_id': None
                }
            )
            reports_created[state_id] = report

        return reports_created

    def create_country_weekly_reports(self, week_number, year, week_start, week_end, state_reports):
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

            # *** Always create/update the country weekly report, even if total_users == 0 ***
            report, created = CountryWeeklyReport.objects.update_or_create(
                week_last_date=week_end,
                country=country,
                week_number=week_number,
                year=year,
                defaults={
                    'week_start_date': week_start,
                    'new_users': total_users,
                    'state_data': state_data
                }
            )
            reports_created[country_id] = report

        return reports_created

    def update_parent_ids(self, village_reports, subdistrict_reports,
                         district_reports, state_reports, country_reports):
        # Set parent_id for village weekly reports
        villages = Village.objects.filter(id__in=village_reports.keys()).select_related('subdistrict')
        for v in villages:
            if v.subdistrict_id in subdistrict_reports:
                vr = village_reports[v.id]
                vr.parent_id = subdistrict_reports[v.subdistrict_id].id
                vr.save()
        # Set parent_id for subdistrict weekly reports
        subs = Subdistrict.objects.filter(id__in=subdistrict_reports.keys()).select_related('district')
        for s in subs:
            if s.district_id in district_reports:
                sr = subdistrict_reports[s.id]
                sr.parent_id = district_reports[s.district_id].id
                sr.save()
        # Set parent_id for district weekly reports
        dists = District.objects.filter(id__in=district_reports.keys()).select_related('state')
        for d in dists:
            if d.state_id in state_reports:
                dr = district_reports[d.id]
                dr.parent_id = state_reports[d.state_id].id
                dr.save()
        # Set parent_id for state weekly reports
        states = State.objects.filter(id__in=state_reports.keys()).select_related('country')
        for s in states:
            if s.country_id in country_reports:
                sr = state_reports[s.id]
                sr.parent_id = country_reports[s.country_id].id
                sr.save()
