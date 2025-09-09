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
        """
        logger.info("Received request to create a PendingUser with data: %s", request.data)
        
        # Extract has_no_initiator flag from request data
        has_no_initiator = request.data.get('has_no_initiator', 'false').lower() == 'true'
        
        # Create a mutable copy of the request data
        data = request.data.copy()
        
        # Only set initiator_id to None if user has no initiator
        if has_no_initiator:
            data['initiator_id'] = None
        else:
            # Ensure initiator_id is preserved when user has an initiator
            initiator_id = data.get('initiator_id')
            if initiator_id is not None and initiator_id != '':
                data['initiator_id'] = initiator_id
            else:
                return Response(
                    {'error': 'Initiator ID is required when has_no_initiator is false'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = PendingUserSerializer(data=data)
        if serializer.is_valid():
            # Create the pending user with the has_no_initiator flag
            pending_user = serializer.save(has_no_initiator=has_no_initiator)
            logger.info(f"PendingUser created with gmail: {pending_user.gmail}")
            
            # Return appropriate response based on initiator status
            if has_no_initiator:
                return Response({
                    'detail': 'Pending user created successfully. Waiting for initiator assignment.',
                    'has_no_initiator': True
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'detail': 'Pending user created successfully.',
                    'has_no_initiator': False
                }, status=status.HTTP_201_CREATED)
        else:
            logger.warning("Invalid PendingUser data: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)