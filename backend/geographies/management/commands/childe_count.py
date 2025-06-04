from django.core.management.base import BaseCommand
from geographies.models.geos import Country, State, District, Subdistrict, Village

class Command(BaseCommand):
    help = 'Calculate and update hierarchical counts for countries, states, districts, and subdistricts'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting hierarchical counts calculation...'))

        # Update number of states in each country
        self.update_country_states()

        # Update number of districts in each state
        self.update_state_districts()

        # Update number of subdistricts in each district
        self.update_district_subdistricts()

        # Update number of villages in each subdistrict
        self.update_subdistrict_villages()

        self.stdout.write(self.style.SUCCESS('Hierarchical counts updated successfully!'))

    def update_country_states(self):
        """Calculate and update the number of states in each country."""
        countries = Country.objects.all()
        for country in countries:
            state_count = State.objects.filter(country=country).count()
            country.number_of_states = state_count
            country.save()
        self.stdout.write(self.style.SUCCESS(f'Updated number of states for {countries.count()} countries.'))

    def update_state_districts(self):
        """Calculate and update the number of districts in each state."""
        states = State.objects.all()
        for state in states:
            district_count = District.objects.filter(state=state).count()
            state.number_of_districts = district_count
            state.save()
        self.stdout.write(self.style.SUCCESS(f'Updated number of districts for {states.count()} states.'))

    def update_district_subdistricts(self):
        """Calculate and update the number of subdistricts in each district."""
        districts = District.objects.all()
        for district in districts:
            subdistrict_count = Subdistrict.objects.filter(district=district).count()
            district.number_of_subdistricts = subdistrict_count
            district.save()
        self.stdout.write(self.style.SUCCESS(f'Updated number of subdistricts for {districts.count()} districts.'))

    def update_subdistrict_villages(self):
        """Calculate and update the number of villages in each subdistrict."""
        subdistricts = Subdistrict.objects.all()
        for subdistrict in subdistricts:
            village_count = Village.objects.filter(subdistrict=subdistrict).count()
            subdistrict.number_of_villages = village_count
            subdistrict.save()
        self.stdout.write(self.style.SUCCESS(f'Updated number of villages for {subdistricts.count()} subdistricts.'))
