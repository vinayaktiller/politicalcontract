from django.core.management.base import BaseCommand
from django.db import transaction, models
from datetime import date
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import (
    VillageDailyReport, SubdistrictDailyReport,
    DistrictDailyReport, StateDailyReport, CountryDailyReport
)
from users.models import Petitioner


class Command(BaseCommand):
    help = 'Generates daily reports for a single day only.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            required=True,
            help='Date in YYYY-MM-DD format'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if report exists'
        )

    def handle(self, *args, **kwargs):
        report_date = date.fromisoformat(kwargs['date'])
        force = kwargs.get('force', False)

        if CountryDailyReport.objects.filter(date=report_date).exists() and not force:
            self.stdout.write(self.style.WARNING(
                f"Report for {report_date} already exists. Use --force to regenerate."
            ))
            return

        # 🧠 Check if any users joined that day
        joined_users = Petitioner.objects.filter(date_joined__date=report_date).exists()

        if not joined_users:
            self.stdout.write(f"No users joined on {report_date}. Creating empty country report...")

            with transaction.atomic():
                countries = Country.objects.all()
                for country in countries:
                    CountryDailyReport.objects.update_or_create(
                        date=report_date,
                        country=country,
                        defaults={
                            'new_users': 0,
                            'state_data': {}
                        }
                    )

            self.stdout.write(self.style.SUCCESS(
                f"✅ Created empty CountryDailyReport for {report_date}"
            ))
            return

        # 🧩 If users joined, generate the full hierarchy
        self.stdout.write(f"Users found on {report_date}. Generating full report...")

        with transaction.atomic():
            village_reports = self.create_village_reports(report_date)
            subdistrict_reports = self.create_subdistrict_reports(report_date, village_reports)
            district_reports = self.create_district_reports(report_date, subdistrict_reports)
            state_reports = self.create_state_reports(report_date, district_reports)
            self.create_country_reports(report_date, state_reports)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully generated daily report for {report_date}"
        ))

    # ============ Helper methods ============

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
                str(u['id']): {
                    "id": str(u['id']),
                    "name": f"{u['first_name']} {u['last_name']}"
                } for u in users
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
        subdistricts = Subdistrict.objects.prefetch_related('village_set')
        subdistrict_reports = {}

        for subdistrict in subdistricts:
            villages = subdistrict.village_set.all()
            total_new_users = 0
            village_data = {}

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
                report, _ = SubdistrictDailyReport.objects.update_or_create(
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
                        vreport = village_reports[village.id]
                        vreport.parent_id = report.id
                        vreport.save()
        return subdistrict_reports

    def create_district_reports(self, report_date, subdistrict_reports):
        districts = District.objects.prefetch_related('subdistrict_set')
        district_reports = {}

        for district in districts:
            subs = district.subdistrict_set.all()
            total_new_users = 0
            sub_data = {}

            for sub in subs:
                report = subdistrict_reports.get(sub.id)
                sub_data[str(sub.id)] = {
                    "id": str(sub.id),
                    "name": sub.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": str(report.id) if report else None
                }
                if report:
                    total_new_users += report.new_users

            if total_new_users > 0:
                report, _ = DistrictDailyReport.objects.update_or_create(
                    date=report_date,
                    district=district,
                    defaults={
                        'new_users': total_new_users,
                        'subdistrict_data': sub_data
                    }
                )
                district_reports[district.id] = report

                for sub in subs:
                    if sub.id in subdistrict_reports:
                        sreport = subdistrict_reports[sub.id]
                        sreport.parent_id = report.id
                        sreport.save()
        return district_reports

    def create_state_reports(self, report_date, district_reports):
        states = State.objects.prefetch_related('district_set')
        state_reports = {}

        for state in states:
            districts = state.district_set.all()
            total_new_users = 0
            dist_data = {}

            for district in districts:
                report = district_reports.get(district.id)
                dist_data[str(district.id)] = {
                    "id": str(district.id),
                    "name": district.name,
                    "new_users": report.new_users if report else 0,
                    "report_id": str(report.id) if report else None
                }
                if report:
                    total_new_users += report.new_users

            if total_new_users > 0:
                report, _ = StateDailyReport.objects.update_or_create(
                    date=report_date,
                    state=state,
                    defaults={
                        'new_users': total_new_users,
                        'district_data': dist_data
                    }
                )
                state_reports[state.id] = report

                for district in districts:
                    if district.id in district_reports:
                        dreport = district_reports[district.id]
                        dreport.parent_id = report.id
                        dreport.save()
        return state_reports

    def create_country_reports(self, report_date, state_reports):
        countries = Country.objects.prefetch_related('state_set')

        for country in countries:
            states = country.state_set.all()
            total_new_users = 0
            state_data = {}

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

            report, _ = CountryDailyReport.objects.update_or_create(
                date=report_date,
                country=country,
                defaults={
                    'new_users': total_new_users,
                    'state_data': state_data
                }
            )

            for state in states:
                if state.id in state_reports:
                    sreport = state_reports[state.id]
                    sreport.parent_id = report.id
                    sreport.save()
