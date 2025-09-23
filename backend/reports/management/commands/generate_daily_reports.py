from django.core.management.base import BaseCommand
from django.db import transaction, models
from datetime import date, timedelta
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

    def handle(self, *args, **kwargs):
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

        while current_date <= end_date:
            if not self.should_skip_date(current_date, kwargs['force']):
                self.generate_reports_for_date(current_date)
                processed_days += 1

                if processed_days % 10 == 0:
                    self.stdout.write(f"Processed {processed_days} days...")

            current_date += timedelta(days=1)

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

    def should_skip_date(self, report_date, force=False):
        if force:
            return False
        return CountryDailyReport.objects.filter(date=report_date).exists()

    def generate_reports_for_date(self, report_date):
        self.stdout.write(f"Processing {report_date}...")

        with transaction.atomic():
            village_reports = self.create_village_reports(report_date)
            subdistrict_reports = self.create_subdistrict_reports(report_date, village_reports)
            district_reports = self.create_district_reports(report_date, subdistrict_reports)
            state_reports = self.create_state_reports(report_date, district_reports)
            self.create_country_reports(report_date, state_reports)

    def create_village_reports(self, report_date):
        villages = Village.objects.annotate(
            new_users_count=models.Count(
                'petitioner',
                filter=models.Q(petitioner__date_joined__date=report_date)
            )
        ).prefetch_related('petitioner_set')

        village_reports = {}
        for village in villages:
            if village.new_users_count == 0:
                continue

            users = village.petitioner_set.filter(
                date_joined__date=report_date
            ).values('id', 'first_name', 'last_name')

            user_data = {
                str(user['id']): {
                    "id": str(user['id']),
                    "name": f"{user['first_name']} {user['last_name']}"
                } for user in users
            }

            report, _ = VillageDailyReport.objects.update_or_create(
                date=report_date,
                village=village,
                defaults={
                    'new_users': village.new_users_count,
                    'user_data': user_data
                }
            )
            village_reports[village.id] = report

        return village_reports

    def create_subdistrict_reports(self, report_date, village_reports):
        subdistricts = Subdistrict.objects.prefetch_related(
            models.Prefetch('village_set', queryset=Village.objects.all())
        )

        subdistrict_reports = {}
        for subdistrict in subdistricts:
            villages = subdistrict.village_set.all()

            village_data = {}
            total_new_users = 0

            for village in villages:
                report = village_reports.get(village.id)
                village_data[str(village.id)] = {
                    "id": str(village.id),
                    "name": village.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": str(report.id) if report else None
                }
                if report:
                    total_new_users += report.new_users

            if total_new_users > 0:
                report, created = SubdistrictDailyReport.objects.update_or_create(
                    date=report_date,
                    subdistrict=subdistrict,
                    defaults={
                        'new_users': total_new_users,
                        'village_data': village_data
                    }
                )
                subdistrict_reports[subdistrict.id] = report

                for village in villages:
                    if village.id in village_reports:
                        village_report = village_reports[village.id]
                        village_report.parent_id = report.id
                        village_report.save()
            else:
                SubdistrictDailyReport.objects.filter(
                    date=report_date,
                    subdistrict=subdistrict
                ).delete()

        return subdistrict_reports

    def create_district_reports(self, report_date, subdistrict_reports):
        districts = District.objects.prefetch_related(
            models.Prefetch('subdistrict_set', queryset=Subdistrict.objects.all())
        )

        district_reports = {}
        for district in districts:
            subdistricts = district.subdistrict_set.all()

            subdistrict_data = {}
            total_new_users = 0

            for sub in subdistricts:
                report = subdistrict_reports.get(sub.id)
                subdistrict_data[str(sub.id)] = {
                    "id": str(sub.id),
                    "name": sub.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": str(report.id) if report else None
                }
                if report:
                    total_new_users += report.new_users

            if total_new_users > 0:
                report, created = DistrictDailyReport.objects.update_or_create(
                    date=report_date,
                    district=district,
                    defaults={
                        'new_users': total_new_users,
                        'subdistrict_data': subdistrict_data
                    }
                )
                district_reports[district.id] = report

                for sub in subdistricts:
                    if sub.id in subdistrict_reports:
                        sub_report = subdistrict_reports[sub.id]
                        sub_report.parent_id = report.id
                        sub_report.save()
            else:
                DistrictDailyReport.objects.filter(
                    date=report_date,
                    district=district
                ).delete()

        return district_reports

    def create_state_reports(self, report_date, district_reports):
        states = State.objects.prefetch_related(
            models.Prefetch('district_set', queryset=District.objects.all())
        )

        state_reports = {}
        for state in states:
            districts = state.district_set.all()

            district_data = {}
            total_new_users = 0

            for district in districts:
                report = district_reports.get(district.id)
                district_data[str(district.id)] = {
                    "id": str(district.id),
                    "name": district.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": str(report.id) if report else None
                }
                if report:
                    total_new_users += report.new_users

            if total_new_users > 0:
                report, created = StateDailyReport.objects.update_or_create(
                    date=report_date,
                    state=state,
                    defaults={
                        'new_users': total_new_users,
                        'district_data': district_data
                    }
                )
                state_reports[state.id] = report

                for district in districts:
                    if district.id in district_reports:
                        dist_report = district_reports[district.id]
                        dist_report.parent_id = report.id
                        dist_report.save()
            else:
                StateDailyReport.objects.filter(
                    date=report_date,
                    state=state
                ).delete()

        return state_reports

    def create_country_reports(self, report_date, state_reports):
        countries = Country.objects.prefetch_related(
            models.Prefetch('state_set', queryset=State.objects.all())
        )

        for country in countries:
            states = country.state_set.all()

            state_data = {}
            total_new_users = 0

            for state in states:
                report = state_reports.get(state.id)
                state_data[str(state.id)] = {
                    "id": str(state.id),
                    "name": state.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": str(report.id) if report else None
                }
                if report:
                    total_new_users += report.new_users

            # Always create (or update) the country report, even if total_new_users == 0
            report, created = CountryDailyReport.objects.update_or_create(
                date=report_date,
                country=country,
                defaults={
                    'new_users': total_new_users,
                    'state_data': state_data
                }
            )

            for state in states:
                if state.id in state_reports:
                    state_report = state_reports[state.id]
                    state_report.parent_id = report.id
                    state_report.save()
