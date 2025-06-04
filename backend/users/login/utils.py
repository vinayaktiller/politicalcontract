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

    This function checks if the provided email corresponds to an existing user in either the 
    `Petitioner` or `PendingUser` database models. It categorizes the user accordingly:
    
    - **'olduser'**: The user exists in the system and has a username.
    - **'pendinguser'**: The user exists in the `PendingUser` model but is not yet registered.
    - **'newuser'**: The user does not exist in either database model.

    Additionally, logging and Prometheus metrics are used to track classification attempts.

    Args:
        email (str): The email address to check against the database.

    Returns:
        tuple: A tuple containing:
            - **user_type (str)**: One of 'olduser', 'pendinguser', or 'newuser'.
            - **user instance or None**: The corresponding user object if found, otherwise None.
    """
    try:
        petitioner = Petitioner.objects.get(gmail=email)
        user_type = 'olduser'
        petitioner.is_online = True
        petitioner.save()
        logger.info(f"User {email} updated {petitioner.is_online}")
        
        # Logging and metrics
        logger.info(f"UserCheck: {email} classified as {user_type}")
        user_check_attempts.labels(user_type=user_type).inc()
        
        return user_type, petitioner

    except Petitioner.DoesNotExist:
        try:
            pending_user = PendingUser.objects.get(gmail=email)
            user_type = 'pendinguser'
            
            # Logging and metrics
            logger.info(f"UserCheck: {email} classified as {user_type}")
            user_check_attempts.labels(user_type=user_type).inc()
            
            return user_type, pending_user

        except PendingUser.DoesNotExist:
            user_type = 'newuser'

            # Logging and metrics
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
