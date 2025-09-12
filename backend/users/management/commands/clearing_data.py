from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management.color import no_style

# Import models
from pendingusers.models.notifications import InitiationNotification
from pendingusers.models.pendinguser import PendingUser
from pendingusers.models.ArchivedPendingUser import ArchivedPendingUser
from users.models.Connectionnotification import ConnectionNotification
from users.models.Circle import Circle
from users.models.usertree import UserTree
from users.models.petitioners import Petitioner
from event.models.groups import Group
from event.models.UserGroupParticipation import UserGroupParticipation
from geographies.models.geos import Country, State, District, Subdistrict, Village



from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Truncates specified tables, resets identities, and sets online_population to NULL for geography models'

    def handle(self, *args, **options):
        # Define tables to truncate with schema and table separated
        tables_to_truncate = [
            # Format: (schema, table)
            ('pendinguser', 'initiationnotification'),
            ('pendinguser', 'archivedpendinguser'),
            ('pendinguser', 'pendinguser'),

            ('userschema', 'connectionnotification'),
            ('userschema', 'petitioner'),
            ('userschema', 'usertree'),
            ('userschema', 'circle'),

            ('event', 'user_group_participation'),
            ('event', 'group'),
        ]

        geography_tables = [
            'country',
            'state',
            'district',
            'subdistrict',
            'village'
        ]

        with transaction.atomic():
            with connection.cursor() as cursor:
                self.stdout.write('Disabling foreign key constraints...')
                cursor.execute('SET CONSTRAINTS ALL DEFERRED')

                for schema, table in tables_to_truncate:
                    full_table = f'"{schema}"."{table}"'
                    self.stdout.write(f'Truncating {full_table}...')
                    cursor.execute(f'TRUNCATE TABLE {full_table} RESTART IDENTITY CASCADE;')

                self.stdout.write('Re-enabling foreign key constraints...')
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')

            with connection.cursor() as cursor:
                for table in geography_tables:
                    self.stdout.write(f'Clearing online_population for {table}...')
                    cursor.execute(f'UPDATE "{table}" SET online_population = NULL;')

        self.stdout.write(self.style.SUCCESS('Operation completed successfully!'))


