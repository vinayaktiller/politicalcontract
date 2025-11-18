# reports/management/commands/delete_weekly_reports.py

from django.core.management.base import BaseCommand
from datetime import date
from reports.models import (
    VillageWeeklyReport, SubdistrictWeeklyReport,
    DistrictWeeklyReport, StateWeeklyReport, CountryWeeklyReport
)

class Command(BaseCommand):
    help = 'Deletes all weekly report records for a given week'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week-last-date',
            type=str,
            required=True,
            help='Week end date (Sunday) in YYYY-MM-DD format for which reports should be deleted'
        )

        parser.add_argument(
            '--force',
            action='store_true',
            help='Confirm deletion without prompting'
        )

    def handle(self, *args, **kwargs):
        target_week_last_date = date.fromisoformat(kwargs['week_last_date'])
        force = kwargs['force']

        if not force:
            confirm = input(f"Are you sure you want to delete all weekly reports for week ending {target_week_last_date}? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        models_to_clear = [
            (CountryWeeklyReport, "CountryWeeklyReport"),
            (StateWeeklyReport, "StateWeeklyReport"),
            (DistrictWeeklyReport, "DistrictWeeklyReport"),
            (SubdistrictWeeklyReport, "SubdistrictWeeklyReport"),
            (VillageWeeklyReport, "VillageWeeklyReport"),
        ]

        total_deleted = 0
        for model, name in models_to_clear:
            deleted, _ = model.objects.filter(week_last_date=target_week_last_date).delete()
            if deleted:
                self.stdout.write(f"Deleted {deleted} from {name}")
                total_deleted += deleted

        if total_deleted == 0:
            self.stdout.write(self.style.WARNING(f"No weekly reports found for week ending {target_week_last_date}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {total_deleted} weekly reports for week ending {target_week_last_date}"))