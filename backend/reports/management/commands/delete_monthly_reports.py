# reports/management/commands/delete_monthly_reports.py

from django.core.management.base import BaseCommand
from datetime import date
from reports.models import (
    VillageMonthlyReport, SubdistrictMonthlyReport,
    DistrictMonthlyReport, StateMonthlyReport, CountryMonthlyReport
)

class Command(BaseCommand):
    help = 'Deletes all monthly report records for a given month'

    def add_arguments(self, parser):
        parser.add_argument(
            '--last-date',
            type=str,
            required=True,
            help='Month end date in YYYY-MM-DD format for which reports should be deleted'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Confirm deletion without prompting'
        )

    def handle(self, *args, **kwargs):
        target_last_date = date.fromisoformat(kwargs['last_date'])
        force = kwargs['force']

        if not force:
            confirm = input(f"Are you sure you want to delete all monthly reports for month ending {target_last_date}? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        models_to_clear = [
            (CountryMonthlyReport, "CountryMonthlyReport"),
            (StateMonthlyReport, "StateMonthlyReport"),
            (DistrictMonthlyReport, "DistrictMonthlyReport"),
            (SubdistrictMonthlyReport, "SubdistrictMonthlyReport"),
            (VillageMonthlyReport, "VillageMonthlyReport"),
        ]

        total_deleted = 0
        for model, name in models_to_clear:
            deleted, _ = model.objects.filter(last_date=target_last_date).delete()
            if deleted:
                self.stdout.write(f"Deleted {deleted} from {name}")
                total_deleted += deleted

        if total_deleted == 0:
            self.stdout.write(self.style.WARNING(f"No monthly reports found for month ending {target_last_date}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {total_deleted} monthly reports for month ending {target_last_date}"))