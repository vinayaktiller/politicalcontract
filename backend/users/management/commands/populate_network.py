import random
import os
import logging
from io import BytesIO
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.core.files import File
from django.utils import timezone
from django.conf import settings
from faker import Faker
from geographies.models.geos import Country, State, District, Subdistrict, Village
from users.models import Petitioner, UserTree
from event.models.groups import Group

logger = logging.getLogger(__name__)
fake = Faker('en_IN')

class Command(BaseCommand):
    help = 'Populates database with hierarchical user network including groups and initiations with historical dates'
    
    # Define where your local profile pictures are stored
    PROFILE_PICS_DIR = os.path.join(settings.BASE_DIR, 'media', 'profile_pics')
    
    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=1000, help='Number of users to create')
        parser.add_argument('--groups', type=int, default=50, help='Number of groups to create')
        parser.add_argument('--flush', action='store_true', help='Delete existing data first')
        parser.add_argument('--days', type=int, default=60, help='Number of days to spread user creation over (default: 60)')
        parser.add_argument('--profile-dir', type=str, default=None, help='Custom directory for profile pictures')
    
    def handle(self, *args, **options):
        user_count = options['users']
        group_count = options['groups']
        flush = options['flush']
        days_spread = options['days']
        
        # Use custom profile directory if provided
        if options['profile_dir']:
            self.PROFILE_PICS_DIR = options['profile_dir']
        
        if flush:
            self.stdout.write("Flushing existing data...")
            Group.objects.all().delete()
            UserTree.objects.all().delete()
            Petitioner.objects.exclude(gmail="root.user@global.net").delete()
            # Reset population counts except root user's village
            Village.objects.all().update(online_population=0)
        
        # Generate date range for user creation - only past 60 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_spread)
        date_list = [start_date + timedelta(days=i) for i in range(days_spread + 1)]
        
        # Retrieve existing root user
        try:
            root_user = Petitioner.objects.get(gmail="vinaydirector527@gmail.com")
            # Adjust root user's join date to beginning of spread
            if root_user.date_joined.date() > start_date:
                root_user.date_joined = datetime.combine(
                    start_date, 
                    datetime.min.time(),
                    tzinfo=timezone.get_current_timezone()
                )
                root_user.save(update_fields=['date_joined'])
        except Petitioner.DoesNotExist:
            raise CommandError('Root user with email "root.user@global.net" not found. Create it first.')
        
        self.stdout.write(f"Using root user: {root_user} (ID: {root_user.id})")
        
        # Create geography if needed
        self.ensure_geography()
        
        # Pre-load local profile pictures
        self.preload_profile_pictures()
        
        # Create other users
        all_users = [root_user]
        villages = list(Village.objects.all())
        
        with transaction.atomic():
            # Create non-root users spread across dates
            for i in range(1, user_count):
                join_date = random.choice(date_list)
                user = self.create_user(villages, i, join_date)
                all_users.append(user)
                if len(all_users) % 100 == 0:
                    self.stdout.write(f"Created {len(all_users)}/{user_count} users")
            
            # Create groups
            groups = []
            for i in range(group_count):
                group = self.create_group(all_users, i)
                groups.append(group)
                if (i + 1) % 10 == 0:
                    self.stdout.write(f"Created {i+1}/{group_count} groups")
            
            # Build user tree
            tree_nodes = [self.ensure_user_tree_node(root_user)]
            for user in all_users[1:]:
                parent = random.choice(tree_nodes)
                event_type = random.choice(['normal', 'private', 'group'])
                event_id = None
                
                if event_type == 'private':
                    event_id = parent.id  # Parent is speaker
                elif event_type == 'group':
                    event_id = random.choice(groups).id  # Random group
                
                node = UserTree.objects.create(
                    id=user.id,
                    normal_id=user.id,
                    name=f"{user.first_name} {user.last_name}"[:255],
                    profilepic=self.get_random_profile_picture(user.id),
                    parentid=parent,
                    event_choice='no_event' if event_type == 'normal' else event_type,
                    event_id=event_id
                )
                tree_nodes.append(node)
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created network with {len(all_users)} users "
            f"spread across {days_spread} days and {len(groups)} groups"
        ))
    
    def preload_profile_pictures(self):
        """Cache the list of available profile pictures"""
        self.profile_pics = []
        
        if not os.path.isdir(self.PROFILE_PICS_DIR):
            logger.warning(f"Profile pictures directory not found: {self.PROFILE_PICS_DIR}")
            return
        
        for filename in os.listdir(self.PROFILE_PICS_DIR):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                self.profile_pics.append(filename)
        
        if not self.profile_pics:
            logger.warning(f"No profile pictures found in {self.PROFILE_PICS_DIR}")
        else:
            logger.info(f"Loaded {len(self.profile_pics)} profile pictures from {self.PROFILE_PICS_DIR}")
    
    def get_random_profile_picture(self, user_id):
        """Get a random profile picture from local files"""
        if not self.profile_pics:
            logger.error("No profile pictures available")
            return None
        
        try:
            # Select a random image file
            filename = random.choice(self.profile_pics)
            file_path = os.path.join(self.PROFILE_PICS_DIR, filename)
            
            # Get file extension
            _, ext = os.path.splitext(filename)
            ext = ext.lstrip('.').lower()  # Remove dot and make lowercase
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = BytesIO(f.read())
            
            # Create filename with user ID
            img_name = f"{user_id}.{ext}"
            return File(content, name=img_name)
        except Exception as e:
            logger.error(f"Error loading profile picture: {e}")
            return None
    
    def ensure_geography(self):
        """Ensure geography hierarchy exists"""
        country, _ = Country.objects.get_or_create(
            name="India",
            defaults={'offline_population': 0, 'online_population': 0}
        )
        
        state, _ = State.objects.get_or_create(
            name="Maharashtra",
            country=country,
            defaults={'offline_population': 0, 'online_population': 0}
        )
        
        district, _ = District.objects.get_or_create(
            name="Pune",
            state=state,
            defaults={'offline_population': 0, 'online_population': 0}
        )
        
        subdistrict, _ = Subdistrict.objects.get_or_create(
            name="Haveli",
            district=district,
            defaults={'offline_population': 0, 'online_population': 0}
        )
        
        village, _ = Village.objects.get_or_create(
            name="Hadapsar",
            subdistrict=subdistrict,
            defaults={
                'status': 'Active',
                'offline_population': 0,
                'online_population': 0
            }
        )
    
    def ensure_user_tree_node(self, user):
        """Ensure root user has a tree node with parentid None"""
        try:
            node = UserTree.objects.get(id=user.id)
            if node.parentid is not None:
                node.parentid = None
                node.save()
            return node
        except UserTree.DoesNotExist:
            return UserTree.objects.create(
                id=user.id,
                normal_id=user.id,
                name=f"{user.first_name} {user.last_name}"[:255],
                profilepic=self.get_random_profile_picture(user.id),
                parentid=None
            )
    
    def create_user(self, villages, index, join_date):
        """Create a new user with village-based ID and specific join date"""
        village = random.choice(villages)
        
        # Update village population
        village.online_population = (village.online_population or 0) + 1
        village.save()
        
        # Generate ID: last 9 digits of village ID + population (5 digits)
        village_id_str = str(village.id)[-9:].zfill(9)
        pop_code = str(village.online_population).zfill(5)
        generated_id = int(village_id_str + pop_code)
        
        # Create random datetime within the join date
        join_datetime = fake.date_time_between_dates(
            datetime_start=datetime.combine(join_date, datetime.min.time()),
            datetime_end=datetime.combine(join_date, datetime.max.time()),
            tzinfo=timezone.get_current_timezone()
        )
        
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
            password=make_password("password123"),
            date_joined=join_datetime
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