# views/phone_number_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny
from pendingusers.models.no_initiator_user import NoInitiatorUser
from pendingusers.models.pendinguser import PendingUser
from .phone_number_serializer import PhoneNumberSerializer
import logging

logger = logging.getLogger(__name__)

class PhoneNumberAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        # Get phone number for a user
        email = request.query_params.get('email')
        
        if not email:
            return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            pending_user = PendingUser.objects.get(gmail=email)
            no_initiator_user = NoInitiatorUser.objects.get(pending_user=pending_user)
            serializer = PhoneNumberSerializer(no_initiator_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PendingUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except NoInitiatorUser.DoesNotExist:
            return Response({"message": "No initiator user record found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        # Update phone number for a user
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        
        if not email or not phone_number:
            return Response({"message": "Email and phone number are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            pending_user = PendingUser.objects.get(gmail=email)
            no_initiator_user = NoInitiatorUser.objects.get(pending_user=pending_user)
            
            serializer = PhoneNumberSerializer(no_initiator_user, data={'phone_number': phone_number})
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Phone number updated for user: {email}")
                return Response({"message": "Phone number updated successfully."}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except PendingUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except NoInitiatorUser.DoesNotExist:
            return Response({"message": "No initiator user record found."}, status=status.HTTP_404_NOT_FOUND)