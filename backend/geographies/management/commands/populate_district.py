import pandas as pd
from django.core.management.base import BaseCommand
from geographies.models.geos import District, State  # Adjust the import if your path is different

class Command(BaseCommand):
    help = 'Populate District model from CSV or Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV or Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            # Auto-detect whether it's CSV or Excel
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            print("Detected column headers:", df.columns)

            districts_to_create = []

            for _, row in df.iterrows():
                # Try to get related State object, if possible
                state = None
                if not pd.isna(row.get('stateid')):  # Check if 'state_id' exists and is not NaN
                    try:
                        state = State.objects.get(id=row['stateid'])
                    except State.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Warning: State with id {row['stateid']} not found for district '{row['name']}'. Leaving state field blank."
                        ))

                district = District(
                    id=row['id'],
                    name=row['name'],
                    state=state
                )
                districts_to_create.append(district)

            # Bulk create all districts at once for speed
            District.objects.bulk_create(districts_to_create, ignore_conflicts=True)

            self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(districts_to_create)} District records'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
