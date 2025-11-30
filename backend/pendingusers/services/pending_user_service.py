import logging
from django.db import transaction
from users.models.petitioners import Petitioner
from users.models.usertree import UserTree
from users.models.AdditionalInfo import AdditionalInfo
from prometheus_client import Counter
from ..models import PendingUser, NoInitiatorUser

pendinguser_verified = Counter(
    'pendinguser_verified_total',
    'Total number of verified pending users'
)

notifications_created = Counter(
    'pendinguser_notifications_created_total',
    'Total number of notifications created during user transfer'
)

logger = logging.getLogger(__name__)

def handle_pending_user_creation(user):
    from ..models.notifications import InitiationNotification
    try:
        if user.initiator_id == 0:
            user.initiator_id = None
            user.is_verified = True
            user.save()
            verify_and_transfer_user(user)
        elif user.initiator_id == None:
            NoInitiatorUser.objects.create(pending_user=user)
            logger.info(f"Created NoInitiatorUser for {user.gmail}")
        elif user.initiator_id:
            initiator = Petitioner.objects.filter(id=user.initiator_id).first()
            if initiator:
                InitiationNotification.objects.create(
                    initiator=initiator,
                    applicant=user
                )
                notifications_created.inc()
    except Exception as e:
        logger.error(f"Error creating initiation notification: {e}")

def update_all_geographical_populations(village):
    """Update population counts for all geographical levels and return sequence numbers"""
    try:
        sequence_numbers = {}
        
        # Update village population
        village.online_population = (village.online_population or 0) + 1
        sequence_numbers['village_number'] = village.online_population
        village.save()
        logger.info(f"Updated village {village.name} population to {village.online_population}")
        
        # Update subdistrict population
        if village.subdistrict:
            subdistrict = village.subdistrict
            subdistrict.online_population = (subdistrict.online_population or 0) + 1
            sequence_numbers['subdistrict_number'] = subdistrict.online_population
            subdistrict.save()
            logger.info(f"Updated subdistrict {subdistrict.name} population to {subdistrict.online_population}")
        else:
            sequence_numbers['subdistrict_number'] = 0
            logger.warning(f"No subdistrict found for village {village.name}")
        
        # Update district population
        if village.subdistrict and village.subdistrict.district:
            district = village.subdistrict.district
            district.online_population = (district.online_population or 0) + 1
            sequence_numbers['district_number'] = district.online_population
            district.save()
            logger.info(f"Updated district {district.name} population to {district.online_population}")
        else:
            sequence_numbers['district_number'] = 0
            logger.warning(f"No district found for village {village.name}")
        
        # Update state population
        if (village.subdistrict and 
            village.subdistrict.district and 
            village.subdistrict.district.state):
            state = village.subdistrict.district.state
            state.online_population = (state.online_population or 0) + 1
            sequence_numbers['state_number'] = state.online_population
            state.save()
            logger.info(f"Updated state {state.name} population to {state.online_population}")
        else:
            sequence_numbers['state_number'] = 0
            logger.warning(f"No state found for village {village.name}")
        
        # Update country population
        if (village.subdistrict and 
            village.subdistrict.district and 
            village.subdistrict.district.state and
            village.subdistrict.district.state.country):
            country = village.subdistrict.district.state.country
            country.online_population = (country.online_population or 0) + 1
            sequence_numbers['country_number'] = country.online_population
            country.save()
            logger.info(f"Updated country {country.name} population to {country.online_population}")
        else:
            sequence_numbers['country_number'] = 0
            logger.warning(f"No country found for village {village.name}")
        
        return sequence_numbers
        
    except Exception as e:
        logger.error(f"Error updating geographical populations: {e}")
        raise

@transaction.atomic
def verify_and_transfer_user(user):
    """Transfer a pending user to Petitioner without deleting notifications or the user itself."""
    try:
        logger.info(f"Processing PendingUser: {user.gmail}")

        # Validate village exists
        if not user.village:
            logger.error(f"PendingUser {user.gmail} does not have a village assigned.")
            raise ValueError("Village is required to generate Petitioner ID.")

        # Update all geographical populations and get sequence numbers
        sequence_numbers = update_all_geographical_populations(user.village)

        # Generate a unique ID
        village_id = str(user.village.id).zfill(9)
        pop_code = str(user.village.online_population).zfill(5)
        generated_id = int(village_id + pop_code)
        logger.info(f"Generated unique ID: {generated_id}")

        # Create Petitioner
        petitioner = Petitioner.objects.create(
            id=generated_id,
            gmail=user.gmail,
            first_name=user.first_name,
            last_name=user.last_name,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            country=user.country,
            state=user.state,
            district=user.district,
            subdistrict=user.subdistrict,
            village=user.village,
        )
        logger.info(f"Created Petitioner with ID: {generated_id}")

        # Create AdditionalInfo record with geographical sequence numbers
        AdditionalInfo.objects.create(
            user_id=generated_id,
            village_number=sequence_numbers['village_number'],
            subdistrict_number=sequence_numbers['subdistrict_number'],
            district_number=sequence_numbers['district_number'],
            state_number=sequence_numbers['state_number'],
            country_number=sequence_numbers['country_number'],
            active_days=0,
            last_active_date=None
        )
        logger.info(f"Created AdditionalInfo for user {generated_id} with sequence numbers: {sequence_numbers}")

        # Determine parent for UserTree
        if user.initiator_id in (0, None):
            logger.info("Creating UserTree without parentid as initiator_id is 0 or None")
            user_tree_data = {
                "id": generated_id,
                "name": user.first_name if len(f"{user.first_name} {user.last_name}") > 15 
                    else f"{user.first_name} {user.last_name}".strip(),
                "profilepic": user.profile_picture,
                # "event_choice": user.event_type,
                # "event_id": user.event_id
            }
        else:
            parent = UserTree.objects.filter(id=user.initiator_id).first()
            if not parent:
                logger.warning(f"No parent found for initiator_id {user.initiator_id}. Proceeding without parent.")
            user_tree_data = {
                "id": generated_id,
                "name": user.first_name if len(f"{user.first_name} {user.last_name}") > 15 
                    else f"{user.first_name} {user.last_name}".strip(),
                "profilepic": user.profile_picture,
                "parentid": parent,  # `parentid` will be None if `parent` does not exist
                "event_choice": user.event_type,
                "event_id": user.event_id
            }

        # Create UserTree entry
        UserTree.objects.create(**user_tree_data)
        logger.info(f"Created UserTree entry for user {generated_id}")

        # Increment verified pending user metric
        pendinguser_verified.inc()

        if user.initiator_id in (0, None):
            pendinguser = PendingUser.objects.filter(gmail=user.gmail).first()
            pendinguser.delete()
            logger.info(f"Deleted PendingUser for {user.gmail} as initiator_id was 0 or None")

        # DO NOT delete notifications or PendingUser instance!

        return petitioner

    except Exception as e:
        logger.error(f"Error verifying/transferring PendingUser: {e}")
        raise