from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Drops specified blog tables from the database'

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
            'user_shared_blog',
        ]

        with transaction.atomic():
            with connection.cursor() as cursor:
                for table in blog_tables:
                    full_table = f'"blog"."{table}"'
                    self.stdout.write(f'Dropping table {full_table}...')
                    cursor.execute(f'DROP TABLE IF EXISTS {full_table} CASCADE;')
        self.stdout.write(self.style.SUCCESS('Specified blog tables dropped successfully!'))
