from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from ...models import Group
from .serializer import GroupSerializer  # Import your GroupSerializer
import logging
from prometheus_client import Counter
from users.login.authentication import CookieJWTAuthentication  # Import your authentication class
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 20
BLOCK_DURATION = 60 * 60  # 1 hour

invalid_attempt_counter = Counter(
    'group_invalid_attempts_total',
    'Total number of invalid group ID attempts per email',
    ['email']
)

email_block_counter = Counter(
    'group_blocked_emails_total',
    'Total number of blocked emails for group validation'
)

class GroupValidationAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_id = request.data.get("group_id")
        email = request.data.get("email")

        logger.debug(f"Received group validation request. Email: {email}, Group ID: {group_id}")

        if not group_id:
            logger.warning(f"Missing group_id in request from {email}")
            return Response({"message": "Group ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        block_key = f"group_block:{email}"
        if cache.get(block_key):
            logger.error(f"Blocked email {email} tried to validate group ID {group_id}")
            return Response({"message": "Too many invalid attempts. Try again later."}, 
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            group = Group.objects.get(id=int(group_id))
            return self._handle_valid_group(group, email, group_id, request)
            
        except (Group.DoesNotExist, ValueError):
            return self._handle_invalid_group(email, group_id)

    def _handle_valid_group(self, group, email, group_id, request):
        # Serialize the group with request context for URL building
        serializer = GroupSerializer(
            group, 
            context={'request': request}
        )
        
        # Reset failure count
        fail_key = f"group_failures:{email}"
        cache.delete(fail_key)
        
        logger.info(f"Successfully validated Group ID {group_id} for email {email}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _handle_invalid_group(self, email, group_id):
        fail_key = f"group_failures:{email}"
        failures = cache.get(fail_key, 0) + 1
        cache.set(fail_key, failures, timeout=BLOCK_DURATION)

        logger.warning(f"Invalid Group ID attempt #{failures} for email {email} (ID: {group_id})")
        invalid_attempt_counter.labels(email=email).inc()

        if failures >= MAX_FAILED_ATTEMPTS:
            block_key = f"group_block:{email}"
            cache.set(block_key, True, timeout=BLOCK_DURATION)
            logger.critical(f"Email {email} blocked after {failures} failed group validation attempts")
            email_block_counter.inc()
            return Response(
                {"message": "Too many invalid attempts. You are temporarily blocked."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        return Response({"message": "Group ID does not exist."}, status=status.HTTP_404_NOT_FOUND)