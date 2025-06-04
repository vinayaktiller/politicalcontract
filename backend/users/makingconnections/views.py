import logging
import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models.petitioners import Petitioner
from ..models.Connectionnotification import ConnectionNotification

# Configure logging
logger = logging.getLogger(__name__)

class CreateConnectionNotification(APIView):
    """
    API view for creating a connection notification.

    This endpoint allows users to initiate a connection request 
    by providing `applicant_id` and `connection_id`.
    """

    def post(self, request):
        """
        Handle POST request to create a connection notification.

        Args:
            request (Request): HTTP request containing JSON data with applicant and connection IDs.

        Returns:
            Response: JSON response confirming the creation of the notification.
        """
        try:
            data = request.data  # Automatically parsed JSON body
            applicant_id = data.get("applicant_id")
            connection_id = data.get("connection_id")

            if not applicant_id or not connection_id:
                logger.warning("Missing required fields in request")
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve applicant and connection
            try:
                applicant = Petitioner.objects.get(id=applicant_id)
                connection = Petitioner.objects.get(id=connection_id)
            except Petitioner.DoesNotExist:
                logger.error(f"Invalid applicant_id ({applicant_id}) or connection_id ({connection_id})")
                return Response({"error": "Invalid applicant or connection ID"}, status=status.HTTP_404_NOT_FOUND)

            # Create a new connection notification
            notification = ConnectionNotification.objects.create(
                applicant=applicant,
                connection=connection,
                
            )

            logger.info(f"Connection notification created successfully (ID: {notification.id})")
            return Response({"message": "Connection notification created successfully!", "notification_id": notification.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error creating connection notification: {str(e)}")
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
