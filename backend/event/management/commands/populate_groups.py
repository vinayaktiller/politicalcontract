# groups/management/commands/populate_groups.py
import random
from django.core.management.base import BaseCommand
from geographies.models.geos import Country, State, District, Subdistrict, Village
from event.models.groups import Group
from users.models.usertree import UserTree

class Command(BaseCommand):
    help = 'Populates groups with sample data using existing UserTree IDs'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, nargs='?', default=5, 
                            help='Number of groups to create (default: 5)')
        parser.add_argument('--founder', type=int, 
                            help='Specific UserTree ID to set as founder for all groups')

    def handle(self, *args, **options):
        count = options['count']
        specific_founder_id = options.get('founder')
        
        # Get existing UserTree IDs
        user_ids = list(UserTree.objects.values_list('id', flat=True))
        
        if not user_ids:
            self.stdout.write(self.style.ERROR('No UserTree objects found in database!'))
            return

        # Get geography objects
        countries = list(Country.objects.all())
        states = list(State.objects.all())
        districts = list(District.objects.all())
        subdistricts = list(Subdistrict.objects.all())
        villages = list(Village.objects.all())

        # Sample data
        group_names = [
            "Farmers Collective", "Sustainable Agriculture Group", 
            "Organic Growers Network", "Crop Innovators Alliance",
            "Rural Development Cooperative", "Agri-Tech Pioneers",
            "Women Farmers Association", "Youth Farming Initiative",
            "Seed Savers Community", "Livestock Keepers Union"
        ]

        institutions = [
            "Ministry of Agriculture", "State Farming Board",
            "University Agriculture Dept", "Farmers Welfare Foundation",
            "International Agri-Council", "Rural Development Trust"
        ]

        # Image URLs from Unsplash (agriculture themed)
        photo_urls = [
            "https://images.unsplash.com/photo-1464226184884-fa280b87c399",
            "https://images.unsplash.com/photo-1492496913980-501348b61469",
            "https://images.unsplash.com/photo-1586771107445-d3ca888129fa",
            "https://images.unsplash.com/photo-1516937941344-00b4e0337589",
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef",
            "https://images.unsplash.com/photo-1556912167-f556f1f39fdf",
            "https://images.unsplash.com/photo-1519750157634-b6d493a0f77c",
            "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7",
            "https://images.unsplash.com/photo-1576675466969-38eeae4b41d9",
            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09"
        ]

        for i in range(count):
            # Select founder
            if specific_founder_id and specific_founder_id in user_ids:
                founder_id = specific_founder_id
            else:
                founder_id = random.choice(user_ids)
            
            # Create speaker list (3-5 speakers including founder)
            num_speakers = random.randint(3, 5)
            available_speakers = [uid for uid in user_ids if uid != founder_id]
            speakers = [founder_id] + random.sample(
                available_speakers,
                min(num_speakers - 1, len(available_speakers))
            )
            
            # Create members list (10-20 members including speakers)
            num_members = random.randint(10, 20)
            all_members = set(speakers)  # Start with speakers
            
            # Add additional members
            available_members = [uid for uid in user_ids if uid not in all_members]
            num_additional = min(num_members - len(all_members), len(available_members))
            if num_additional > 0:
                all_members.update(random.sample(available_members, num_additional))
            
            members = list(all_members)
            
            # Create outside agents (1-3 agents, not including founder)
            available_agents = [uid for uid in user_ids if uid != founder_id]
            outside_agents = random.sample(
                available_agents, 
                min(random.randint(1, 3), len(available_agents))
            )

            # Create group
            group = Group.objects.create(
                name=f"{random.choice(group_names)} #{i+1}",
                founder=founder_id,
                profile_pic=random.choice(photo_urls),
                speakers=speakers,
                members=members,
                outside_agents=outside_agents,
                country=random.choice(countries) if countries else None,
                state=random.choice(states) if states else None,
                district=random.choice(districts) if districts else None,
                subdistrict=random.choice(subdistricts) if subdistricts else None,
                village=random.choice(villages) if villages else None,
                institution=random.choice(institutions),
                links=[f"https://group-website-{i+1}.example.com"],
                photos=random.sample(photo_urls, min(5, len(photo_urls))),
                # pending_speakers left as default empty list
            )

            self.stdout.write(self.style.SUCCESS(
                f'Created group: "{group.name}" with founder {founder_id} '
                f'({len(speakers)} speakers, {len(members)} members)'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {count} groups!\n'
            f'Used only existing UserTree IDs for all user references\n'
            f'Profile pictures from: Unsplash.com'
        ))