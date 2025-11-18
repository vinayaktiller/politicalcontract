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
from ...models import PendingUser, NoInitiatorUser, PendingVerificationNotification, RejectedPendingUser
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
                # ONLY update NoInitiatorUser - leave PendingUser unchanged
                no_initiator_data.verification_status = "verified"
                no_initiator_data.verified_by = current_usertree
                no_initiator_data.save()

                response_data = {
                    "message": "User marked as verified. Petitioner will be created when user accepts.",
                    # "petitioner": {
                    #     "id": petitioner.id,
                    #     "gmail": petitioner.gmail,
                    #     "first_name": petitioner.first_name,
                    #     "last_name": petitioner.last_name,
                    #     "date_of_birth": petitioner.date_of_birth,
                    #     "gender": petitioner.gender,
                    #     "country": petitioner.country.name if petitioner.country else None,
                    #     "state": petitioner.state.name if petitioner.state else None,
                    #     "district": petitioner.district.name if petitioner.district else None,
                    #     "subdistrict": petitioner.subdistrict.name if petitioner.subdistrict else None,
                    #     "village": petitioner.village.name if petitioner.village else None,
                    # },
                    # "user_tree": {
                    #     "id": user_tree.id,
                    #     "name": user_tree.name,
                    #     "profilepic": user_tree.profilepic.url if user_tree.profilepic else None,
                    #     "parentid": user_tree.parentid.id if user_tree.parentid else None,
                    #     "event_choice": user_tree.event_choice,
                    #     "event_id": user_tree.event_id,
                    # }
                }

                # Create notification but DON'T delete the user data yet
                # profile_pic_url = user_tree.profilepic.url if user_tree.profilepic else None
                # pending_notification = PendingVerificationNotification.objects.create(
                #     user_email=pending_user.gmail,
                #     generated_user_id=petitioner.id,
                #     name=user_tree.name,
                #     profile_pic=profile_pic_url
                # )

                # # If user is online, send immediately after creation
                # is_online = self.is_user_online(pending_user.gmail)
                
                self.send_verification_notification(
                        pending_user.gmail,
                        # petitioner.id,
                        # user_tree.name,
                        # profile_pic_url,
                        pending_user.id  # Send pending_user_id for later cleanup
                    )
                    # Optionally mark delivered if sending is successful:
                # pending_notification.delivered = True
                # pending_notification.save()

                # # DON'T delete the NoInitiatorUser and PendingUser instances here
                # # They will be cleaned up when user clicks OK in frontend

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def is_user_online(self, user_email):
        """Check if user is currently connected to WebSocket"""
        return cache.get(f"user_online_{user_email}", False)
        
    def send_verification_notification(self, user_email, pending_user_id):
        # user_id, name, profile_pic, pending_user_id
        """Send WebSocket notification to the user about verification"""
        try:
            channel_layer = get_channel_layer()
            sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', user_email)
            group_name = f"waiting_{sanitized_email}"
            
            message = {
                "type": "admin_verification",
                "status": "verified",
                "message": "🎉 Congratulations! Your account has been verified by our team.",
                # "generated_user_id": user_id,
                # "name": name,
                # "profile_pic": profile_pic or "",
                "pending_user_id": pending_user_id  # Include for cleanup
            }
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "admin_verification_message",
                    "message": message
                }
            )
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {str(e)}")

class RejectPendingUser(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, user_id):
        with transaction.atomic():
            pending_user = get_object_or_404(
                PendingUser.objects.select_for_update(),
                id=user_id,
                initiator_id__isnull=True
            )
            no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
            
            try:
                current_usertree = UserTree.objects.get(id=request.user.id)
            except UserTree.DoesNotExist:
                return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

            # Check if claimed by this user (or allow superuser to reject any)
            if no_initiator_data and no_initiator_data.claimed_by != current_usertree and not request.user.is_superuser:
                return Response({"error": "You can only reject users you've claimed"}, status=status.HTTP_403_FORBIDDEN)

            # Get rejection reason from request
            rejection_reason = request.data.get('rejection_reason', '')

            try:
                # First, mark the user as rejected in NoInitiatorUser
                if no_initiator_data:
                    no_initiator_data.verification_status = "rejected"
                    no_initiator_data.notes = f"Rejected by admin {current_usertree.id}. Reason: {rejection_reason}"
                    no_initiator_data.save()

                # Create rejected user record for archiving
                rejected_user = RejectedPendingUser.objects.create(
                    gmail=pending_user.gmail,
                    first_name=pending_user.first_name,
                    last_name=pending_user.last_name,
                    profile_picture=pending_user.profile_picture.url if pending_user.profile_picture else None,
                    date_of_birth=pending_user.date_of_birth,
                    gender=pending_user.gender,
                    country_id=pending_user.country.id if pending_user.country else None,
                    country_name=pending_user.country.name if pending_user.country else None,
                    state_id=pending_user.state.id if pending_user.state else None,
                    state_name=pending_user.state.name if pending_user.state else None,
                    district_id=pending_user.district.id if pending_user.district else None,
                    district_name=pending_user.district.name if pending_user.district else None,
                    subdistrict_id=pending_user.subdistrict.id if pending_user.subdistrict else None,
                    subdistrict_name=pending_user.subdistrict.name if pending_user.subdistrict else None,
                    village_id=pending_user.village.id if pending_user.village else None,
                    village_name=pending_user.village.name if pending_user.village else None,
                    rejected_by=current_usertree,
                    rejection_reason=rejection_reason,
                    original_pending_user_id=pending_user.id,
                    event_type=pending_user.event_type,
                    is_online=pending_user.is_online
                )

                # Send rejection notification to user - DON'T delete yet
                self.send_rejection_notification(
                    pending_user.gmail,
                    rejection_reason,
                    pending_user.id  # Send pending_user_id for cleanup
                )

                return Response({
                    "message": "User rejected successfully. Notification sent to user.", 
                    "rejected_user_id": rejected_user.id,
                    "pending_user_id": pending_user.id
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def send_rejection_notification(self, user_email, rejection_reason, pending_user_id):
        """Send WebSocket notification to the user about rejection"""
        try:
            channel_layer = get_channel_layer()
            sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', user_email)
            group_name = f"waiting_{sanitized_email}"
            
            message = {
                "type": "admin_verification",  # Same type as verification
                "status": "rejected",  # Different status
                "message": "❌ Your application has been rejected by our team.",
                "pending_user_id": pending_user_id,
                "rejection_reason": rejection_reason or "No reason provided"
            }
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "admin_verification_message",  # Same handler as verification
                    "message": message
                }
            )
            logger.info(f"Rejection notification sent to {user_email}, group: {group_name}")
        except Exception as e:
            logger.error(f"Failed to send rejection WebSocket notification: {str(e)}")