import os
import random
import logging
from io import BytesIO
from datetime import datetime
from django.db import transaction
from django.core.files import File
from django.utils import timezone
from django.conf import settings
from faker import Faker
from celery import shared_task
from geographies.models.geos import Village
from users.models import Petitioner, UserTree
from event.models.groups import Group

from .models import Milestone

logger = logging.getLogger(__name__)
fake = Faker('en_IN')

# Preload profile pictures list once when the worker starts
PROFILE_PICS_DIR = os.path.join(settings.BASE_DIR, 'media', 'profile_pics')
PROFILE_PICS = []

# Load profile pictures at worker startup
def preload_profile_pictures():
    global PROFILE_PICS
    if not os.path.isdir(PROFILE_PICS_DIR):
        logger.warning(f"Profile pictures directory not found: {PROFILE_PICS_DIR}")
        return
    
    for filename in os.listdir(PROFILE_PICS_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            PROFILE_PICS.append(filename)
    
    if not PROFILE_PICS:
        logger.warning(f"No profile pictures found in {PROFILE_PICS_DIR}")
    else:
        logger.info(f"Preloaded {len(PROFILE_PICS)} profile pictures")

# Preload when module is imported
preload_profile_pictures()

def get_random_profile_picture(user_id):
    """Get a random profile picture from preloaded files"""
    if not PROFILE_PICS:
        logger.error("No profile pictures available")
        return None
    
    try:
        # Select a random image file
        filename = random.choice(PROFILE_PICS)
        file_path = os.path.join(PROFILE_PICS_DIR, filename)
        
        # Get file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lstrip('.').lower()
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = BytesIO(f.read())
        
        # Create filename with user ID
        img_name = f"{user_id}.{ext}"
        return File(content, name=img_name)
    except Exception as e:
        logger.error(f"Error loading profile picture: {e}")
        return None

def create_live_user():
    """Create single user with realistic live data"""
    villages = list(Village.objects.all())
    if not villages:
        logger.error("No villages available for user creation")
        return None
    
    village = random.choice(villages)
    
    # Lock and update village population
    village = Village.objects.select_for_update().get(id=village.id)
    village.online_population = (village.online_population or 0) + 1
    village.save()
    
    # Generate unique ID: last 9 digits of village ID + population (5 digits)
    village_id_str = str(village.id)[-9:].zfill(9)
    pop_code = str(village.online_population).zfill(5)
    generated_id = int(village_id_str + pop_code)
    
    # Create user data
    gender = random.choice(['M', 'F', 'O'])
    first_name = fake.first_name_male() if gender == 'M' else fake.first_name_female()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}{generated_id}@live.example.com"
    
    # Ensure unique email (should be rare but possible)
    while Petitioner.objects.filter(gmail=email).exists():
        generated_id += 1
        email = f"{first_name.lower()}.{last_name.lower()}{generated_id}@live.example.com"
    
    return Petitioner.objects.create(
        id=generated_id,
        gmail=email,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
        gender=gender,
        country=village.subdistrict.district.state.country,
        state=village.subdistrict.district.state,
        district=village.subdistrict.district,
        subdistrict=village.subdistrict,
        village=village,
        password="live_pass123",  # Will be hashed in save()
        date_joined=timezone.now()
    )

@shared_task
def add_live_users():
    try:
        with transaction.atomic():
            # Randomize user count (1-5 users per minute)
            user_count = random.randint(1, 5)
            groups = list(Group.objects.all())
            tree_nodes = list(UserTree.objects.all())
            
            if not tree_nodes:
                logger.error("No parent nodes available")
                return

            new_users = []
            for _ in range(user_count):
                # Create user
                user = create_live_user()
                if not user:
                    continue
                    
                # Create tree node with random parent
                parent = random.choice(tree_nodes)
                
                # Determine event type with weights
                event_type = random.choices(
                    ['normal', 'private', 'group'], 
                    weights=[70, 20, 10],  # 70% normal, 20% private, 10% group
                    k=1
                )[0]
                
                event_id = None
                if event_type == 'private':
                    event_id = parent.id  # Parent is speaker
                elif event_type == 'group' and groups:
                    event_id = random.choice(groups).id  # Random group
                
                # Create UserTree node
                node = UserTree.objects.create(
                    id=user.id,
                    normal_id=user.id,
                    name=f"{user.first_name} {user.last_name}"[:255],
                    profilepic=get_random_profile_picture(user.id),
                    parentid=parent,
                    event_choice='no_event' if event_type == 'normal' else event_type,
                    event_id=event_id
                )
                tree_nodes.append(node)
                new_users.append(user.id)
            
            logger.info(f"Created {len(new_users)} live users: {new_users}")
        return f"Added {user_count} users"
    except Exception as e:
        logger.error(f"Live user creation failed: {str(e)}", exc_info=True)
        raise


@shared_task
def populate_milestones_sequence():
    """Populates milestones for a user in the correct sequence"""
    user_id = 11021801300001  # Your target user ID
    
    # Get the milestone definitions from UserTree
    initiation_milestones = UserTree.INITIATION_MILESTONES
    influence_milestones = UserTree.INFLUENCE_MILESTONES
    
    try:
        # Get existing milestones for the user
        existing_milestones = Milestone.objects.filter(user_id=user_id)
        existing_titles = [m.title for m in existing_milestones]
        
        # Create a list of all possible milestones in order
        all_milestones = []
        
        # Add initiation milestones in order
        for threshold in sorted(initiation_milestones.keys()):
            title, text = initiation_milestones[threshold]
            all_milestones.append({
                'type': 'initiation',
                'title': title,
                'text': text,
                'threshold': threshold
            })
        
        # Add influence milestones in order
        for threshold in sorted(influence_milestones.keys()):
            title, text = influence_milestones[threshold]
            all_milestones.append({
                'type': 'influence',
                'title': title,
                'text': text,
                'threshold': threshold
            })
        
        # Find the next milestone to create
        next_milestone = None
        for milestone in all_milestones:
            if milestone['title'] not in existing_titles:
                next_milestone = milestone
                break
        
        if not next_milestone:
            # If all milestones exist, reset by deleting them
            existing_milestones.delete()
            next_milestone = all_milestones[0]  # Start from the first one
            logger.info("Reset milestones for new sequence")
        
        # Get user's gender for photo ID calculation
        try:
            from .models.petitioners import Petitioner
            petitioner = Petitioner.objects.get(id=user_id)
            gender = petitioner.gender
        except Petitioner.DoesNotExist:
            gender = 'M'  # Default to male
        
        # Calculate photo ID based on milestone type and gender
        if next_milestone['type'] == 'initiation':
            levels = sorted(initiation_milestones.keys())
            milestone_index = levels.index(next_milestone['threshold'])
            gender_offset = 0 if gender == 'M' else 1
            photo_id = milestone_index * 2 + gender_offset + 1
        else:  # influence
            levels = sorted(influence_milestones.keys())
            milestone_index = levels.index(next_milestone['threshold'])
            gender_offset = 0 if gender == 'M' else 1
            photo_id = milestone_index * 2 + gender_offset + 1
        
        # Create the milestone
        Milestone.objects.create(
            user_id=user_id,
            title=next_milestone['title'],
            text=next_milestone['text'],
            type=next_milestone['type'],
            photo_id=photo_id,
            created_at=timezone.now()
        )
        
        logger.info(f"Created milestone: {next_milestone['title']}")
        return f"Created {next_milestone['type']} milestone: {next_milestone['title']}"
    
    except Exception as e:
        logger.error(f"Error creating milestone sequence: {str(e)}")
        raise