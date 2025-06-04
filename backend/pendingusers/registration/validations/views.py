from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication  # Updated authentication
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from users.models.usertree import UserTree
from .serializer import InitiatorIdSerializer
from prometheus_client import Counter
import logging

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = 20
BLOCK_DURATION = 60 * 60

invalid_attempt_counter = Counter(
    'initiator_invalid_attempts_total',
    'Total number of invalid initiator ID attempts per email',
    ['email']
)

email_block_counter = Counter(
    'initiator_blocked_emails_total',
    'Total number of blocked emails'
)

class ValidateInitiatorAPIView(APIView):
    authentication_classes = [JWTAuthentication]  # Changed to JWT authentication
    permission_classes = [IsAuthenticated]

    def post(self, request):
        initiator_id = request.data.get("initiator_id")
        email = request.data.get("email")

        logger.debug(f"Received initiator validation request. Email: {email}, ID: {initiator_id}")

        if not initiator_id:
            logger.warning(f"Missing initiator_id in request from {email}")
            return Response({"message": "Initiator ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        block_key = f"block:{email}"
        if cache.get(block_key):
            logger.error(f"Blocked email {email} tried to validate initiator ID {initiator_id}")
            return Response({"message": "Too many invalid attempts. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            initiator = UserTree.objects.get(id=int(initiator_id))
            serializer = InitiatorIdSerializer(initiator, context={'request': request})
            fail_key = f"failures:{email}"
            cache.delete(fail_key)
            logger.info(f"Successfully validated Initiator ID {initiator_id} for email {email}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UserTree.DoesNotExist:
            fail_key = f"failures:{email}"
            failures = cache.get(fail_key, 0) + 1
            cache.set(fail_key, failures, timeout=BLOCK_DURATION)

            logger.warning(f"Invalid Initiator ID attempt #{failures} for email {email} (ID: {initiator_id})")
            invalid_attempt_counter.labels(email=email).inc()

            if failures >= MAX_FAILED_ATTEMPTS:
                cache.set(block_key, True, timeout=BLOCK_DURATION)
                logger.critical(f"Email {email} has been blocked after {failures} failed attempts")
                email_block_counter.inc()
                return Response(
                    {"message": "Too many invalid attempts. You are temporarily blocked."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            return Response({"message": "Initiator ID does not exist."}, status=status.HTTP_404_NOT_FOUND)