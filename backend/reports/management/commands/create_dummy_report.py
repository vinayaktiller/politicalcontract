from django.core.management.base import BaseCommand
from datetime import date
from geographies.models.geos import State, Country
from reports.models import StateDailyReport, CountryDailyReport

class Command(BaseCommand):
    help = "Creates a dummy StateDailyReport and CountryDailyReport for a given date (default: 2025-09-12)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default='2025-09-12',
            help='Date in YYYY-MM-DD format (default: 2025-09-12)'
        )

    def handle(self, *args, **kwargs):
        report_date = date.fromisoformat(kwargs['date'])

        # Pick any one state (for testing)
        state = State.objects.first()
        if not state:
            self.stdout.write(self.style.ERROR("No states found in database."))
            return

        self.stdout.write(f"Creating dummy report for {state.name} on {report_date}...")

        # Create state report with zero users
        state_report, created = StateDailyReport.objects.update_or_create(
            date=report_date,
            state=state,
            defaults={
                'new_users': 0,
                'district_data': {}
            }
        )

        # Create/Update corresponding country-level report
        country = state.country
        country_report, _ = CountryDailyReport.objects.update_or_create(
            date=report_date,
            country=country,
            defaults={
                'new_users': 0,
                'state_data': {str(state.id): {
                    "id": str(state.id),
                    "name": state.name,
                    "new_users": 0,
                    "report_id": str(state_report.id)
                }}
            }
        )

        state_report.parent_id = country_report.id
        state_report.save()

        self.stdout.write(self.style.SUCCESS(
            f"Dummy report created for {state.name} on {report_date}"
        ))
