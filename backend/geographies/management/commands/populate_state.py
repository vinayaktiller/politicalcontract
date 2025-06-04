import pandas as pd
from django.core.management.base import BaseCommand
from geographies.models.geos import State, Country

class Command(BaseCommand):
    help = 'Populate State model from Excel (.xlsx) file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            # Load the Excel file
            df = pd.read_excel(file_path)

            print("Detected column headers:", df.columns)

            for _, row in df.iterrows():
                country, _ = Country.objects.get_or_create(id=row['contry'])

                state = State(
                    id=row['id'],
                    name=row['name'],
                    country=country,
                )
                state.save()

            self.stdout.write(self.style.SUCCESS('Successfully populated State model'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
