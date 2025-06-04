import pandas as pd
from django.core.management.base import BaseCommand
from geographies.models.geos import Village, Subdistrict  # Import correct models

class Command(BaseCommand):
    help = 'Populate Village model from CSV or Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV or Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            # Load the file based on its extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            print("Detected column headers:", df.columns)

            villages_to_create = []

            for _, row in df.iterrows():
                subdistrict = None
                if not pd.isna(row.get('subdistrictid')):  # Expecting 'subdistrictid' column
                    try:
                        subdistrict = Subdistrict.objects.get(id=row['subdistrictid'])
                    except Subdistrict.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Warning: Subdistrict with id {row['subdistrictid']} not found for village '{row['name']}'. Leaving subdistrict field blank."
                        ))

                village = Village(
                    id=row['id'],
                    name=row['name '],
                    status=row['status'],
                    
                    subdistrict=subdistrict,
                )
                villages_to_create.append(village)

            # Bulk create for efficiency
            Village.objects.bulk_create(villages_to_create, ignore_conflicts=True)

            self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(villages_to_create)} Village records'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
