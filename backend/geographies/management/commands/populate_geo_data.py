from django.core.management.base import BaseCommand
import pandas as pd
from geographies.models.geos import State, District, Subdistrict, Village, Country
from django.db import transaction
from tqdm import tqdm

BATCH_SIZE = 5000

class Command(BaseCommand):
    help = 'Populate the database from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **kwargs):
        
        file_path = kwargs['file_path']
        df = pd.read_excel(file_path)

        country, created = Country.objects.get_or_create(name="India")

        states = []
        districts = []
        subdistricts = []
        villages = []

        total_rows = len(df)

        for index, row in tqdm(df.iterrows(), total=total_rows, desc="Processing data"):
            # Populate State
            state, created = State.objects.get_or_create(
                name=row['State Name'],
                country=country
            )

            # Populate District
            district, created = District.objects.get_or_create(
                name=row['District Name'],
                state=state
            )

            # Populate Subdistrict
            subdistrict, created = Subdistrict.objects.get_or_create(
                name=row['Sub-District Name'],
                district=district
            )

            # Create a Village for every row without duplicate checks
            village = Village(
                name=row['Village Name'],
                subdistrict=subdistrict,
                status=row.get('Village Status', None)
            )
            villages.append(village)

            states.append(state)
            districts.append(district)
            subdistricts.append(subdistrict)

            if (index + 1) % BATCH_SIZE == 0:
                self.bulk_insert(states, districts, subdistricts, villages)
                states.clear()
                districts.clear()
                subdistricts.clear()
                villages.clear()

        if states or districts or subdistricts or villages:
            self.bulk_insert(states, districts, subdistricts, villages)

        self.stdout.write(self.style.SUCCESS(f'Data population complete. Processed {total_rows} rows.'))

    def bulk_insert(self, states, districts, subdistricts, villages):
        with transaction.atomic():
            # Insert all villages, allowing duplicates if model permits
            State.objects.bulk_create(states, ignore_conflicts=True)
            District.objects.bulk_create(districts, ignore_conflicts=True)
            Subdistrict.objects.bulk_create(subdistricts, ignore_conflicts=True)
            Village.objects.bulk_create(villages, ignore_conflicts=True)