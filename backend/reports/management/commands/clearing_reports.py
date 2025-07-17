from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Truncates user, geography, event, and report-related tables, resets sequences, and clears data safely.'

    def handle(self, *args, **options):
        tables_to_truncate = [
            # Reports: Village
            ('report', 'village_daily_report'),
            ('report', 'village_weekly_report'),
            ('report', 'village_monthly_report'),

            # Reports: Subdistrict
            ('report', 'subdistrict_daily_report'),
            ('report', 'subdistrict_weekly_report'),
            ('report', 'subdistrict_monthly_report'),

            # Reports: District
            ('report', 'district_daily_report'),
            ('report', 'district_weekly_report'),
            ('report', 'district_monthly_report'),

            # Reports: State
            ('report', 'state_daily_report'),
            ('report', 'state_weekly_report'),
            ('report', 'state_monthly_report'),

            # Reports: Country
            ('report', 'country_daily_report'),
            ('report', 'country_weekly_report'),
            ('report', 'country_monthly_report'),

            # Cumulative report
            ('report', 'cumulative_report'),
        ]

        

        with transaction.atomic():
            with connection.cursor() as cursor:
                self.stdout.write(self.style.WARNING('Disabling foreign key constraints...'))
                cursor.execute('SET CONSTRAINTS ALL DEFERRED')

                for schema, table in tables_to_truncate:
                    full_table = f'"{schema}"."{table}"'
                    self.stdout.write(self.style.NOTICE(f'Truncating {full_table}...'))
                    cursor.execute(f'TRUNCATE TABLE {full_table} RESTART IDENTITY CASCADE;')

                self.stdout.write(self.style.SUCCESS('Re-enabling foreign key constraints...'))
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')

        self.stdout.write(self.style.SUCCESS('All specified tables have been truncated successfully.'))
