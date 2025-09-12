# views.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
import json
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from ...models import PendingUser, NoInitiatorUser, PendingVerificationNotification
from ..serializers import PendingUserNoInitiatorSerializer
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from users.permissions.permissions import IsSuperUser
from rest_framework.pagination import PageNumberPagination
from users.models.usertree import UserTree
import logging

logger = logging.getLogger(__name__)

class VerifyPendingUser(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, user_id):
        with transaction.atomic():
            pending_user = get_object_or_404(
                PendingUser.objects.select_for_update(),
                id=user_id,
                initiator_id__isnull=True
            )

            # Check if there's a NoInitiatorUser record
            no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
            if not no_initiator_data:
                return Response({"error": "No initiator data found"}, status=status.HTTP_404_NOT_FOUND)

            try:
                current_usertree = UserTree.objects.get(id=request.user.id)
            except UserTree.DoesNotExist:
                return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

            # Check if claimed by this user
            if no_initiator_data.claimed_by != current_usertree:
                return Response({"error": "You need to claim this user first"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Set initiator and initiation type before verification
                pending_user.initiator_id = current_usertree.id
                pending_user.event_type = 'online'
                pending_user.save()

                # Verify and transfer (returns only Petitioner here)
                petitioner = pending_user.verify_and_transfer()

                # Retrieve the corresponding UserTree by petitioner's id
                try:
                    user_tree = UserTree.objects.get(id=petitioner.id)
                except UserTree.DoesNotExist:
                    return Response({"error": "UserTree entry not created"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                response_data = {
                    "message": "User verified and transferred successfully",
                    "petitioner": {
                        "id": petitioner.id,
                        "gmail": petitioner.gmail,
                        "first_name": petitioner.first_name,
                        "last_name": petitioner.last_name,
                        "date_of_birth": petitioner.date_of_birth,
                        "gender": petitioner.gender,
                        "country": petitioner.country.name if petitioner.country else None,
                        "state": petitioner.state.name if petitioner.state else None,
                        "district": petitioner.district.name if petitioner.district else None,
                        "subdistrict": petitioner.subdistrict.name if petitioner.subdistrict else None,
                        "village": petitioner.village.name if petitioner.village else None,
                    },
                    "user_tree": {
                        "id": user_tree.id,
                        "name": user_tree.name,
                        "profilepic": user_tree.profilepic.url if user_tree.profilepic else None,
                        "parentid": user_tree.parentid.id if user_tree.parentid else None,
                        "event_choice": user_tree.event_choice,
                        "event_id": user_tree.event_id,
                    }
                }

                # Always create notification
                profile_pic_url = user_tree.profilepic.url if user_tree.profilepic else None
                pending_notification = PendingVerificationNotification.objects.create(
                    user_email=pending_user.gmail,
                    generated_user_id=petitioner.id,
                    name=user_tree.name,
                    profile_pic=profile_pic_url
                )

                # If user is online, send immediately after creation
                is_online = self.is_user_online(pending_user.gmail)
                if is_online:
                    self.send_verification_notification(
                        pending_user.gmail,
                        petitioner.id,
                        user_tree.name,
                        profile_pic_url
                    )
                    # Optionally mark delivered if sending is successful:
                    pending_notification.delivered = True
                    pending_notification.save()

                # Delete the NoInitiatorUser and PendingUser instances
                no_initiator_data.delete()
                pending_user.delete()

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def is_user_online(self, user_email):
        """Check if user is currently connected to WebSocket"""
        return cache.get(f"user_online_{user_email}", False)
        
    def send_verification_notification(self, user_email, user_id, name, profile_pic):
        """Send WebSocket notification to the user about verification"""
        try:
            channel_layer = get_channel_layer()
            sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', user_email)
            group_name = f"waiting_{sanitized_email}"
            
            message = {
                "type": "admin_verification",
                "status": "verified",
                "message": "🎉 Congratulations! Your account has been verified by our team.",
                "generated_user_id": user_id,
                "name": name,
                "profile_pic": profile_pic or ""
            }
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "admin_verification_message",
                    "message": message  # Send as dict, not JSON string
                }
            )
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {str(e)}")