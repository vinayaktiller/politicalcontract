import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from pendingusers.models import PendingUser
from .serializers import PendingUserSerializer

logger = logging.getLogger(__name__)


class PendingUserCreateView(APIView):
    """
    Handles creation of a PendingUser instance.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Create a PendingUser from POST data.
        Expects fields like gmail, first_name, last_name, date_of_birth, gender,
        location (country/state/district/subdistrict/village), and optionally profile_picture.
        """
        logger.info("Received request to create a PendingUser with data: %s", request.data)
        serializer = PendingUserSerializer(data=request.data)
        if serializer.is_valid():
            pending_user = serializer.save()
            logger.info(f"PendingUser created with gmail: {pending_user.gmail}")
            return Response({'detail': 'Pending user created successfully.'}, status=status.HTTP_201_CREATED)
        else:
            logger.warning("Invalid PendingUser data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
