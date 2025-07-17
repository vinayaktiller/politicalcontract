import random
import requests
import logging
from io import BytesIO
from django.core import management
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from geographies.models.geos import Country, State, District, Subdistrict, Village
from users.models.petitioners import Petitioner
from users.models.usertree import UserTree

logger = logging.getLogger(__name__)
fake = Faker()

class Command(BaseCommand):
    help = 'Populates database with fake user data including profile pictures'
    
    def add_arguments(self, parser):
        parser.add_argument('count', type=int, nargs='?', default=50,
                            help='Number of fake users to create (default: 50)')
    
    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f"Creating {count} fake users...")
        
        # Ensure we have geographical data
        self.populate_geographies()
        
        # Get all villages for random selection
        villages = list(Village.objects.all())
        if not villages:
            self.stderr.write("No villages found! Please load geographical data first.")
            return
            
        # Get existing UserTree entries for parents
        available_parents = list(UserTree.objects.all())
        
        with transaction.atomic():
            created_users = []
            for i in range(count):
                # Create root user for first 5 if no parents available
                parent = None
                if available_parents:
                    parent = random.choice(available_parents) if random.random() > 0.3 else None
                
                user, user_tree = self.create_fake_user(villages, parent)
                created_users.append(user)
                available_parents.append(user_tree)
                
                # Progress indicator
                if (i+1) % 10 == 0:
                    self.stdout.write(f"Created {i+1}/{count} users...")
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully created {len(created_users)} fake users with profile pictures!"
            ))
    
    def populate_geographies(self):
        """Ensure we have geographical data"""
        if not Country.objects.exists():
            management.call_command('loaddata', 'geographies/fixtures/geographies.json')
    
    def create_fake_user(self, villages, parent_user_tree=None):
        # Select random village and update population
        village = random.choice(villages)
        village.online_population = (village.online_population or 0) + 1
        village.save()
        
        # Generate unique ID
        village_id = str(village.id).zfill(9)
        pop_code = str(village.online_population).zfill(5)
        generated_id = int(village_id + pop_code)
        
        # Create fake data
        first_name = fake.first_name()
        last_name = fake.last_name()
        gender = random.choice(['M', 'F', 'O'])
        
        # Create Petitioner
        petitioner = Petitioner.objects.create(
            id=generated_id,
            gmail=fake.unique.email(),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
            gender=gender,
            country=village.subdistrict.district.state.country,
            state=village.subdistrict.district.state,
            district=village.subdistrict.district,
            subdistrict=village.subdistrict,
            village=village,
        )
        
        # Download and save profile picture
        profile_pic = self.download_profile_picture(generated_id)
        
        # Create UserTree
        display_name = first_name if len(f"{first_name} {last_name}") > 15 else f"{first_name} {last_name}"
        
        user_tree = UserTree.objects.create(
            id=generated_id,
            normal_id=generated_id,
            name=display_name.strip(),
            profilepic=profile_pic,
            parentid=parent_user_tree,
            childcount=0,
            influence=0
        )
        
        return petitioner, user_tree
    
    def download_profile_picture(self, user_id):
        """Download random profile picture from online service"""
        try:
            # Use different avatar services for variety
            services = [
                f"https://i.pravatar.cc/300?u={user_id}",
                f"https://robohash.org/{user_id}?set=set4",
                f"https://api.dicebear.com/7.x/identicon/svg?seed={user_id}"
            ]
            
            response = requests.get(random.choice(services))
            response.raise_for_status()
            
            img_name = f"{user_id}.jpg"
            img_file = BytesIO(response.content)
            
            return File(img_file, name=img_name)
        except Exception as e:
            logger.error(f"Error downloading profile picture: {e}")
            return None