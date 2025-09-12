from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Truncates user, geography, event, and report-related tables (including activity reports), resets sequences, and clears data safely.'

    def handle(self, *args, **options):
        tables_to_truncate = [
            # =========================
            # OLD 'report' SCHEMA TABLES
            # =========================

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
            

            # =========================
            # NEW 'activity_reports' TABLES
            # =========================

            # Village Activity
            ('activity_reports', 'daily_village_activity_report'),
            ('activity_reports', 'weekly_village_activity_report'),
            ('activity_reports', 'monthly_village_activity_report'),

            # Subdistrict Activity
            ('activity_reports', 'daily_subdistrict_activity_report'),
            ('activity_reports', 'weekly_subdistrict_activity_report'),
            ('activity_reports', 'monthly_subdistrict_activity_report'),

            # District Activity
            ('activity_reports', 'daily_district_activity_report'),
            ('activity_reports', 'weekly_district_activity_report'),
            ('activity_reports', 'monthly_district_activity_report'),

            # State Activity
            ('activity_reports', 'daily_state_activity_report'),
            ('activity_reports', 'weekly_state_activity_report'),
            ('activity_reports', 'monthly_state_activity_report'),

            # Country Activity
            ('activity_reports', 'daily_country_activity_report'),
            ('activity_reports', 'weekly_country_activity_report'),
            ('activity_reports', 'monthly_country_activity_report'),

            # User Activity
            ('activity_reports', 'user_monthly_activity'),
            ('activity_reports', 'daily_activity_summary'),
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
