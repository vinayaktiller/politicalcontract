import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from notifications.login_push.services.push_notifications import handle_user_notifications_on_login
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models.petitioners import Petitioner

logger = logging.getLogger(__name__)

class LoginPushNotificationAPIView(APIView):
    """
    API View to trigger login push notification after validating Petitioner instance via user_id.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Extract user ID from request body
            user_id = request.data.get("user_id")
            if not user_id:
                logger.warning("Missing user_id in request.")
                return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Validate Petitioner instance by user ID
            try:
                petitioner = Petitioner.objects.get(id=user_id)
                logger.info(f"Valid Petitioner found: {petitioner.gmail}")

            except Petitioner.DoesNotExist:
                logger.warning(f"No Petitioner found with ID: {user_id}")
                return Response({"error": "Invalid user ID."}, status=status.HTTP_404_NOT_FOUND)

            # Call function to send login notification
            handle_user_notifications_on_login(petitioner)
            logger.debug(f"Login notification sent successfully for {petitioner.gmail}")

            return Response({"message": "Login notification triggered successfully."}, status=status.HTTP_200_OK)

        except AuthenticationFailed as auth_error:
            logger.error(f"Authentication error: {auth_error}")
            return Response({"error": str(auth_error)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            logger.critical(f"Unexpected error in LoginPushNotificationAPIView: {e}", exc_info=True)
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)