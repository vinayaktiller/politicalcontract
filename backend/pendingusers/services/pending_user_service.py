import logging
from django.db import transaction
from users.models.petitioners import Petitioner
from users.models.usertree import UserTree
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

@transaction.atomic
def verify_and_transfer_user(user):
    """Transfer a pending user to Petitioner without deleting notifications or the user itself."""
    try:
        logger.info(f"Processing PendingUser: {user.gmail}")

        # Validate village exists
        if not user.village:
            logger.error(f"PendingUser {user.gmail} does not have a village assigned.")
            raise ValueError("Village is required to generate Petitioner ID.")

        # Update village population
        user.village.online_population = (user.village.online_population or 0) + 1
        user.village.save()

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

        # Increment verified pending user metric
        pendinguser_verified.inc()

        # DO NOT delete notifications or PendingUser instance!

        return petitioner

    except Exception as e:
        logger.error(f"Error verifying/transferring PendingUser: {e}")
        raise
