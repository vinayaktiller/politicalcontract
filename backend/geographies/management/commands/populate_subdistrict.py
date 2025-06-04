import pandas as pd
from django.core.management.base import BaseCommand
from geographies.models.geos import Subdistrict, District  # Notice: District now, not State

class Command(BaseCommand):
    help = 'Populate Subdistrict model from CSV or Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV or Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            # Load the file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            print("Detected column headers:", df.columns)

            for _, row in df.iterrows():
                district = None
                if not pd.isna(row.get('districtid')):  # Expecting column name 'districtid'
                    try:
                        district = District.objects.get(id=row['districtid'])
                    except District.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Warning: District with id {row['districtid']} not found for subdistrict '{row['name']}'. Leaving district field blank."
                        ))

                subdistrict = Subdistrict(
                    id=row['id'],
                    name=row['name'],
                    district=district,
                )
                subdistrict.save()

            self.stdout.write(self.style.SUCCESS('Successfully populated Subdistrict model'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
