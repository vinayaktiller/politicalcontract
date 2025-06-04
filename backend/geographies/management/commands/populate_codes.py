from django.core.management.base import BaseCommand
from geographies.models.geos import State, District, Subdistrict, Village


class Command(BaseCommand):
    help = "Populate geocode fields hierarchically across State, District, Subdistrict, and Village models"

    def handle(self, *args, **kwargs):
        # Populate state_geocode_id in District
        self.stdout.write("Populating state_geocode_id in District model...")
        districts = District.objects.select_related('state')
        for district in districts:
            if district.state and district.state.geo_code is not None:
                district.state_geocode_id = district.state.geo_code
                district.save()
        self.stdout.write("Completed populating state_geocode_id.")

        # Populate district_geocode_id in Subdistrict
        self.stdout.write("Populating district_geocode_id in Subdistrict model...")
        subdistricts = Subdistrict.objects.select_related('district')
        for subdistrict in subdistricts:
            if subdistrict.district and subdistrict.district.geo_code is not None:
                subdistrict.district_geocode_id = subdistrict.district.geo_code
                subdistrict.save()
        self.stdout.write("Completed populating district_geocode_id.")

        # Populate subdistrict_geocode_id in Village
        self.stdout.write("Populating subdistrict_geocode_id in Village model...")
        villages = Village.objects.select_related('subdistrict')
        for village in villages:
            if village.subdistrict and village.subdistrict.geo_code is not None:
                village.subdistrict_geocode_id = village.subdistrict.geo_code
                village.save()
        self.stdout.write("Completed populating subdistrict_geocode_id.")
