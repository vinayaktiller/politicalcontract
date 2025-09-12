import random
import requests
import logging
from io import BytesIO
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.core.files import File
from faker import Faker
from geographies.models.geos import Country, State, District, Subdistrict, Village
from users.models import Petitioner, UserTree
from event.models.groups import Group

logger = logging.getLogger(__name__)
fake = Faker('en_IN')

class Command(BaseCommand):
    help = 'Populates database with hierarchical user network including groups and initiations'
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=100, help='Number of users to create')
        parser.add_argument('--groups', type=int, default=10, help='Number of groups to create')
        parser.add_argument('--flush', action='store_true', help='Delete existing data first')
    
    def handle(self, *args, **options):
        user_count = options['users']
        group_count = options['groups']
        flush = options['flush']
        
        if flush:
            self.stdout.write("Flushing existing data...")
            Group.objects.all().delete()
            UserTree.objects.all().delete()
            Petitioner.objects.all().delete()
        
        # Ensure root user exists
        root_user = self.ensure_root_user()
        self.stdout.write(f"Root user: {root_user} (ID: {root_user.id})")
        
        # Create geography if needed
        root_village = self.ensure_geography()
        
        # Create other users
        all_users = [root_user]
        villages = list(Village.objects.all())
        
        with transaction.atomic():
            # Create non-root users
            for i in range(1, user_count):
                user = self.create_user(villages, i)
                all_users.append(user)
                if len(all_users) % 10 == 0:
                    self.stdout.write(f"Created {len(all_users)}/{user_count} users")
            
            # Create groups
            groups = []
            for i in range(group_count):
                group = self.create_group(all_users, i)
                groups.append(group)
                self.stdout.write(f"Created group: {group.name}")
            
            # Build user tree with different initiation types
            tree_nodes = [self.ensure_user_tree_node(root_user)]
            for user in all_users[1:]:
                parent = random.choice(tree_nodes)
                event_type = random.choice(['normal', 'private', 'group'])
                event_id = None
                
                if event_type == 'private':
                    # Private event - parent is the speaker
                    event_id = parent.id
                elif event_type == 'group':
                    # Group event - assign to random group
                    event_id = random.choice(groups).id
                
                node = UserTree.objects.create(
                    id=user.id,
                    normal_id=user.id,
                    name=f"{user.first_name} {user.last_name}"[:255],
                    profilepic=self.download_profile_picture(user.id),
                    parentid=parent,
                    event_choice='no_event' if event_type == 'normal' else event_type,
                    event_id=event_id
                )
                tree_nodes.append(node)
                self.stdout.write(f"Created tree node for {user.first_name} with {event_type} initiation")
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created network with {len(all_users)} users and {len(groups)} groups"
        ))
    
    def ensure_geography(self):
        """Ensure geography hierarchy exists"""
        country, created = Country.objects.get_or_create(
            name="India",
            defaults={
                'offline_population': 0,
                'online_population': 0,
                'number_of_states': 0
            }
        )
        
        state, created = State.objects.get_or_create(
            name="Maharashtra",
            country=country,
            defaults={
                'offline_population': 0,
                'online_population': 0,
                'number_of_districts': 0
            }
        )
        
        district, created = District.objects.get_or_create(
            name="Pune",
            state=state,
            defaults={
                'offline_population': 0,
                'online_population': 0,
                'number_of_subdistricts': 0
            }
        )
        
        subdistrict, created = Subdistrict.objects.get_or_create(
            name="Haveli",
            district=district,
            defaults={
                'offline_population': 0,
                'online_population': 0,
                'number_of_villages': 0
            }
        )
        
        village, created = Village.objects.get_or_create(
            name="Hadapsar",
            subdistrict=subdistrict,
            defaults={
                'status': 'Active',
                'offline_population': 0,
                'online_population': 0
            }
        )
        
        return village
    
    def ensure_root_user(self):
        """Ensure root user exists with fixed ID"""
        root_id = 11081701500001
        try:
            return Petitioner.objects.get(id=root_id)
        except Petitioner.DoesNotExist:
            return Petitioner.objects.create(
                id=root_id,
                gmail="root.user@global.net",
                first_name="Global",
                last_name="Root",
                date_of_birth=date(1980, 1, 1),
                gender="O",
                country=Country.objects.get(name="India"),
                state=State.objects.get(name="Maharashtra"),
                district=District.objects.get(name="Pune"),
                subdistrict=Subdistrict.objects.get(name="Haveli"),
                village=Village.objects.get(name="Hadapsar"),
                password=make_password("securepassword123")
            )
    
    def ensure_user_tree_node(self, user):
        """Ensure root user has a tree node"""
        try:
            return UserTree.objects.get(id=user.id)
        except UserTree.DoesNotExist:
            return UserTree.objects.create(
                id=user.id,
                normal_id=user.id,
                name="Global Root",
                profilepic=self.download_profile_picture(user.id),
                parentid=None
            )
    
    def create_user(self, villages, index):
        """Create a new user with village-based ID"""
        village = random.choice(villages)
        village.online_population = (village.online_population or 0) + 1
        village.save()
        
        # Generate ID: village ID (9 digits) + population (5 digits)
        village_id = str(village.id).zfill(9)
        pop_code = str(village.online_population).zfill(5)
        generated_id = int(village_id + pop_code)
        
        # Create user data
        gender = random.choice(['M', 'F', 'O'])
        first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
        last_name = fake.last_name()
        
        return Petitioner.objects.create(
            id=generated_id,
            gmail=f"{first_name.lower()}.{last_name.lower()}{index}@example.com",
            first_name=first_name,
            last_name=last_name,
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
            gender=gender,
            country=village.subdistrict.district.state.country,
            state=village.subdistrict.district.state,
            district=village.subdistrict.district,
            subdistrict=village.subdistrict,
            village=village,
            password=make_password("password123")
        )
    
    def create_group(self, users, index):
        """Create a group with random founder and members"""
        group_types = ['School', 'College', 'Organization', 'Community', 'Club']
        group_subtypes = {
            'School': ['Elementary', 'High', 'International'],
            'College': ['Engineering', 'Medical', 'Arts'],
            'Organization': ['NGO', 'Non-Profit', 'Volunteer'],
            'Community': ['Religious', 'Cultural', 'Neighborhood'],
            'Club': ['Sports', 'Book', 'Hobby']
        }
        
        group_type = random.choice(group_types)
        founder = random.choice(users)
        subtype = random.choice(group_subtypes[group_type])
        
        # Get geography from founder
        return Group.objects.create(
            name=f"{subtype} {group_type} {index+1}",
            founder=founder.id,
            profile_pic=f"https://picsum.photos/300/200?group={index}",
            speakers=[founder.id],
            country=founder.country,
            state=founder.state,
            district=founder.district,
            subdistrict=founder.subdistrict,
            village=founder.village,
            institution=fake.company(),
            links=[
                f"https://www.{fake.domain_name()}",
                f"https://{fake.slug()}.org"
            ],
            photos=[
                f"https://picsum.photos/400/300?group={index}-1",
                f"https://picsum.photos/400/300?group={index}-2",
                f"https://picsum.photos/400/300?group={index}-3"
            ]
        )
    
    def download_profile_picture(self, user_id):
        """Download random profile picture"""
        try:
            services = [
                f"https://i.pravatar.cc/300?u={user_id}",
                f"https://robohash.org/{user_id}?set=set4",
                f"https://api.dicebear.com/7.x/identicon/svg?seed={user_id}"
            ]
            response = requests.get(random.choice(services))
            response.raise_for_status()
            
            img_name = f"{user_id}.jpg"
            return File(BytesIO(response.content), name=img_name)
        except Exception as e:
            logger.error(f"Error downloading profile picture: {e}")
            return None