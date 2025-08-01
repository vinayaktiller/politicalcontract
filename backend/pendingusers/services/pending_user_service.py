import logging
from django.db import transaction
from users.models.petitioners import Petitioner
from users.models.usertree import UserTree
from prometheus_client import Counter

pendinguser_verified = Counter(
    'pendinguser_verified_total',
    'Total number of verified pending users'
)
notifications_deleted = Counter(
    'pendinguser_notifications_deleted_total',
    'Total number of notifications deleted during user transfer'
)

logger = logging.getLogger(__name__)

def handle_pending_user_creation(user):
    from ..models.notifications import InitiationNotification
    try:
        if user.initiator_id in (0, None):
            user.initiator_id = None
            user.is_verified = True
            user.save()
            user.verify_and_transfer()
        elif user.initiator_id:
            initiator = Petitioner.objects.filter(id=user.initiator_id).first()
            if initiator:
                InitiationNotification.objects.create(
                    initiator=initiator,
                    applicant=user
                )
    except Exception as e:
        logger.error(f"Error creating initiation notification: {e}")

def delete_related_notifications(pending_user):
    from ..models.notifications import InitiationNotification
    """Delete all initiation notifications related to the pending user."""
    try:
        count, _ = InitiationNotification.objects.filter(applicant=pending_user).delete()
        notifications_deleted.inc(count)
        logger.info(f"Deleted {count} notifications for pending user {pending_user.gmail}")
    except Exception as e:
        logger.error(f"Error deleting notifications for {pending_user.gmail}: {e}")
        raise

@transaction.atomic
def verify_and_transfer_user(user):
    """Transfer a pending user to Petitioner after cleaning up notifications."""
    try:
        logger.info(f"Processing PendingUser: {user.gmail}")

        # Step 1: Clean up notifications
        delete_related_notifications(user)

        # Step 2: Validate village exists
        if not user.village:
            logger.error(f"PendingUser {user.gmail} does not have a village assigned.")
            raise ValueError("Village is required to generate Petitioner ID.")

        # Step 3: Update village population
        user.village.online_population = (user.village.online_population or 0) + 1
        user.village.save()

        # Step 4: Generate a unique ID
        village_id = str(user.village.id).zfill(9)
        pop_code = str(user.village.online_population).zfill(5)
        generated_id = int(village_id + pop_code)
        logger.info(f"Generated unique ID: {generated_id}")

        # Step 5: Create Petitioner
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

        # Step 6: Determine parent for UserTree
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

        # Step 7: Create UserTree entry
        UserTree.objects.create(**user_tree_data)

        # Step 8: Update metrics and delete PendingUser
        pendinguser_verified.inc()
        user.delete()

        return petitioner

    except Exception as e:
        logger.error(f"Error verifying/transferring PendingUser: {e}")
        raise
