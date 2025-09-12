import logging
from prometheus_client import Counter
from rest_framework_simplejwt.tokens import RefreshToken
from users.models.petitioners import Petitioner
from pendingusers.models import PendingUser

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
user_check_attempts = Counter('user_check_attempts', 'Total number of user lookup attempts', ['user_type'])

def UserCheck(email):
    """
    Determines the user's type based on their email.

    Categories:
    - 'pendinguser': If user exists in both Petitioner and PendingUser, or only PendingUser with initiator.
    - 'no_initiator': If user exists in PendingUser but has no initiator.
    - 'olduser': If user exists only in Petitioner.
    - 'newuser': If user does not exist in either.

    Returns:
        tuple: (user_type, user_instance or None)
    """
    petitioner = Petitioner.objects.filter(gmail=email).first()
    pending_user = PendingUser.objects.filter(gmail=email).first()

    if pending_user:
        # Check if initiator is null
        if pending_user.initiator_id is None:
            user_type = 'no_initiator'
            logger.info(f"UserCheck: {email} classified as {user_type} (no initiator)")
            user_check_attempts.labels(user_type=user_type).inc()
            return user_type, pending_user
        else:
            user_type = 'pendinguser'
            logger.info(f"UserCheck: {email} classified as {user_type}")
            user_check_attempts.labels(user_type=user_type).inc()
            return user_type, pending_user

    elif petitioner:
        # If only in Petitioner, classify as 'olduser'
        user_type = 'olduser'
        petitioner.is_online = True
        petitioner.save()
        logger.info(f"User {email} updated is_online = {petitioner.is_online}")
        logger.info(f"UserCheck: {email} classified as {user_type}")
        user_check_attempts.labels(user_type=user_type).inc()
        return user_type, petitioner
    
    
    

    else:
        # Not found in either
        user_type = 'newuser'
        logger.info(f"UserCheck: {email} classified as {user_type}")
        user_check_attempts.labels(user_type=user_type).inc()
        return user_type, None


def get_tokens_for_user(user):
    """
    Generates authentication tokens for a given user.

    Args:
        user (User): The user instance for whom tokens are to be generated.

    Returns:
        dict: A dictionary containing refresh and access tokens.
    """
    refresh = RefreshToken.for_user(user)
    tokens = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

    # Logging
    logger.info(f"Tokens generated for user ID: {user.id}")

    return tokens
