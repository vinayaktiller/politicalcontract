from django.core.management.base import BaseCommand
from datetime import date
from reports.models import (
    VillageDailyReport, SubdistrictDailyReport,
    DistrictDailyReport, StateDailyReport, CountryDailyReport
)

class Command(BaseCommand):
    help = 'Deletes all daily report records for a given date'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            required=True,
            help='Date in YYYY-MM-DD format for which reports should be deleted'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Confirm deletion without prompting'
        )

    def handle(self, *args, **kwargs):
        target_date = date.fromisoformat(kwargs['date'])
        force = kwargs['force']

        if not force:
            confirm = input(f"Are you sure you want to delete all daily reports for {target_date}? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        models_to_clear = [
            (CountryDailyReport, "CountryDailyReport"),
            (StateDailyReport, "StateDailyReport"),
            (DistrictDailyReport, "DistrictDailyReport"),
            (SubdistrictDailyReport, "SubdistrictDailyReport"),
            (VillageDailyReport, "VillageDailyReport"),
        ]

        total_deleted = 0
        for model, name in models_to_clear:
            deleted, _ = model.objects.filter(date=target_date).delete()
            if deleted:
                self.stdout.write(f"Deleted {deleted} from {name}")
                total_deleted += deleted

        if total_deleted == 0:
            self.stdout.write(self.style.WARNING(f"No reports found for {target_date}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {total_deleted} reports for {target_date}"))
