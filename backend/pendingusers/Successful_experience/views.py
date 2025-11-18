from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated  # Optional: add authentication if needed
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import logging

from ..models.notifications import InitiationNotification
from pendingusers.models import PendingUser
from users.models import Petitioner, UserTree
from users.profilepic_manager.utils import get_profilepic_url

logger = logging.getLogger(__name__)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Uncomment if authentication is required
def verify_user_response(request):
    try:
        data = request.data
        notification_id = data.get("notificationId")
        response_val = data.get("response")
        gmail = data.get("gmail")

        if not notification_id or response_val is None or not gmail:
            return Response(
                {"error": "Missing 'notificationId', 'response' or 'gmail'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Confirm PendingUser exists early
        try:
            _ = PendingUser.objects.get(gmail=gmail)
        except PendingUser.DoesNotExist:
            return Response({"error": "PendingUser not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            try:
                notification = InitiationNotification.objects.select_for_update().get(id=notification_id)
            except InitiationNotification.DoesNotExist:
                return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

            petitioner = None

            if response_val.lower() == "yes":
                petitioner = notification.mark_as_verified()
            elif response_val.lower() == "no":
                notification.mark_as_rejected()
            else:
                return Response({"error": "Invalid response value"}, status=status.HTTP_400_BAD_REQUEST)

            response_data = {
                "status": "success",
                "message": "Verification processed"
            }

            if petitioner:
                try:
                    user_tree = UserTree.objects.get(id=petitioner.id)
                except UserTree.DoesNotExist:
                    user_tree = None

                profile_picture_url = get_profilepic_url(user_tree, request)

                response_data["user"] = {
                    "id": petitioner.id,
                    "name": user_tree.name if user_tree else "",
                    "profile_picture": profile_picture_url,
                }

            return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing verification: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)