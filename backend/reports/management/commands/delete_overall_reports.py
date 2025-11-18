# reports/management/commands/delete_overall_reports.py

from django.core.management.base import BaseCommand
from reports.models import OverallReport

class Command(BaseCommand):
    help = 'Deletes all overall report records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Confirm deletion without prompting'
        )

    def handle(self, *args, **kwargs):
        force = kwargs['force']

        total_reports = OverallReport.objects.count()

        if total_reports == 0:
            self.stdout.write(self.style.WARNING('No overall reports found.'))
            return

        if not force:
            confirm = input(f"Are you sure you want to delete ALL {total_reports} overall reports? This cannot be undone. (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        deleted_count = OverallReport.objects.all().delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f'Successfully deleted {deleted_count} overall reports'
        ))