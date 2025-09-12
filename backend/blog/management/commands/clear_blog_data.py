from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Truncates all blog tables and resets identities'

    def handle(self, *args, **options):
        blog_tables = [
            'blog_load',
            'base_blog_model',
            'comment',
            'consumption_micro',
            'consumption_short_essay',
            'consumption_article',
            'failed_initiation_experience_micro',
            'failed_initiation_experience_short_essay',
            'failed_initiation_experience_article',
            'journey_blog_micro',
            'journey_blog_short_essay',
            'journey_blog_article',
            'milestone_journey_micro',
            'milestone_journey_short_essay',
            'milestone_journey_article',
            'report_insight_micro',
            'report_insight_short_essay',
            'report_insight_article',
            'successful_experience_micro',
            'successful_experience_short_essay',
            'successful_experience_article',
            'answering_question_blog_micro',
            'answering_question_blog_short_essay',
            'answering_question_blog_article',
        ]

        with transaction.atomic():
            with connection.cursor() as cursor:
                self.stdout.write('Disabling foreign key constraints...')
                cursor.execute('SET CONSTRAINTS ALL DEFERRED')

                for table in blog_tables:
                    full_table = f'"blog"."{table}"'
                    self.stdout.write(f'Truncating {full_table}...')
                    cursor.execute(f'TRUNCATE TABLE {full_table} RESTART IDENTITY CASCADE;')

                self.stdout.write('Re-enabling foreign key constraints...')
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')

        self.stdout.write(self.style.SUCCESS('All blog tables cleaned successfully!'))
