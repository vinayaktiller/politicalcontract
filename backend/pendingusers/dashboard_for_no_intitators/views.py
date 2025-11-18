from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from ..models import PendingUser, NoInitiatorUser
from .serializers import PendingUserNoInitiatorSerializer
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from users.permissions.permissions import IsSuperUser
from rest_framework.pagination import PageNumberPagination
from users.models.usertree import UserTree
from ..models import PendingUser, NoInitiatorUser, RejectedPendingUser  # Add RejectedPendingUser
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
import re
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)



class PendingUserNoInitiatorPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class PendingUserNoInitiatorListView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperUser]
    pagination_class = PendingUserNoInitiatorPagination

    def get(self, request):
        pending_users = PendingUser.objects.filter(
            initiator_id__isnull=True
        ).select_related(
            'no_initiator_data',
            'no_initiator_data__claimed_by',
        ).order_by('-id')

        verification_status = request.query_params.get('verification_status', None)
        if verification_status:
            pending_users = pending_users.filter(
                no_initiator_data__verification_status=verification_status
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(pending_users, request)

        if page is not None:
            serializer = PendingUserNoInitiatorSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PendingUserNoInitiatorSerializer(pending_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ClaimPendingUser(APIView):
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
            if not no_initiator_data:
                return Response({"error": "No initiator data found"}, status=status.HTTP_404_NOT_FOUND)

            try:
                current_usertree = UserTree.objects.get(id=request.user.id)
            except UserTree.DoesNotExist:
                return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

            # Check if already claimed
            if no_initiator_data.verification_status == "claimed":
                if no_initiator_data.claimed_by == current_usertree:
                    return Response({"message": "Already claimed by you"}, status=status.HTTP_200_OK)
                return Response({"error": "Already claimed by another admin"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user is already verified or marked as spam
            if no_initiator_data.verification_status in ["verified", "spam"]:
                return Response({"error": "Cannot claim a user that is already verified or marked as spam"}, status=status.HTTP_400_BAD_REQUEST)

            # Claim the user
            no_initiator_data.verification_status = "claimed"
            no_initiator_data.claimed_by = current_usertree
            no_initiator_data.claimed_at = timezone.now()
            no_initiator_data.save()

            return Response({"message": "User claimed successfully"}, status=status.HTTP_200_OK)


# class VerifyPendingUser(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def post(self, request, user_id):
#         with transaction.atomic():
#             pending_user = get_object_or_404(
#                 PendingUser.objects.select_for_update(),
#                 id=user_id,
#                 initiator_id__isnull=True
#             )

#             # Check if there's a NoInitiatorUser record
#             no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
#             if not no_initiator_data:
#                 return Response({"error": "No initiator data found"}, status=status.HTTP_404_NOT_FOUND)

#             try:
#                 current_usertree = UserTree.objects.get(id=request.user.id)
#             except UserTree.DoesNotExist:
#                 return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

#             # Check if claimed by this user
#             if no_initiator_data.claimed_by != current_usertree:
#                 return Response({"error": "You need to claim this user first"}, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 # Set initiator and initiation type before verification
#                 pending_user.initiator_id = current_usertree.id
#                 pending_user.event_type = 'online'
#                 pending_user.save()

#                 # Verify and transfer (returns only Petitioner here)
#                 petitioner = pending_user.verify_and_transfer()

#                 # Retrieve the corresponding UserTree by petitioner's id
#                 try:
#                     user_tree = UserTree.objects.get(id=petitioner.id)
#                 except UserTree.DoesNotExist:
#                     return Response({"error": "UserTree entry not created"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#                 # Prepare response data
#                 response_data = {
#                     "message": "User verified and transferred successfully",
#                     "petitioner": {
#                         "id": petitioner.id,
#                         "gmail": petitioner.gmail,
#                         "first_name": petitioner.first_name,
#                         "last_name": petitioner.last_name,
#                         "date_of_birth": petitioner.date_of_birth,
#                         "gender": petitioner.gender,
#                         "country": petitioner.country.name if petitioner.country else None,
#                         "state": petitioner.state.name if petitioner.state else None,
#                         "district": petitioner.district.name if petitioner.district else None,
#                         "subdistrict": petitioner.subdistrict.name if petitioner.subdistrict else None,
#                         "village": petitioner.village.name if petitioner.village else None,
#                     },
#                     "user_tree": {
#                         "id": user_tree.id,
#                         "name": user_tree.name,
#                         "profilepic": user_tree.profilepic.url if user_tree.profilepic else None,
#                         "parentid": user_tree.parentid.id if user_tree.parentid else None,
#                         "event_choice": user_tree.event_choice,
#                         "event_id": user_tree.event_id,
#                     }
#                 }

#                 # Delete the NoInitiatorUser and PendingUser instances
#                 no_initiator_data.delete()
#                 pending_user.delete()

#                 return Response(response_data, status=status.HTTP_200_OK)

#             except Exception as e:
#                 return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnclaimPendingUser(APIView):
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
            if not no_initiator_data:
                return Response({"error": "No initiator data found"}, status=status.HTTP_404_NOT_FOUND)

            try:
                current_usertree = UserTree.objects.get(id=request.user.id)
            except UserTree.DoesNotExist:
                return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

            if no_initiator_data.claimed_by != current_usertree and not request.user.is_superuser:
                return Response({"error": "You can only unclaim your own claims"}, status=status.HTTP_403_FORBIDDEN)

            # Unclaim the user
            no_initiator_data.verification_status = "unclaimed"
            no_initiator_data.claimed_by = None
            no_initiator_data.claimed_at = None
            no_initiator_data.save()

            return Response({"message": "User unclaimed successfully"}, status=status.HTTP_200_OK)

class UpdatePendingUserNotes(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsSuperUser]

    def patch(self, request, user_id):
        pending_user = get_object_or_404(PendingUser, id=user_id, initiator_id__isnull=True)
        no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
        if not no_initiator_data:
            return Response({"error": "No initiator data found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            current_usertree = UserTree.objects.get(id=request.user.id)
        except UserTree.DoesNotExist:
            return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

        if no_initiator_data.claimed_by != current_usertree and not request.user.is_superuser:
            return Response({"error": "You can only update notes for users you've claimed"}, status=status.HTTP_403_FORBIDDEN)

        notes = request.data.get('notes', '')
        no_initiator_data.notes = notes
        no_initiator_data.save()

        return Response({"message": "Notes updated successfully"}, status=status.HTTP_200_OK)

class MarkAsSpam(APIView):
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
            if not no_initiator_data:
                return Response({"error": "No initiator data found"}, status=status.HTTP_404_NOT_FOUND)

            try:
                current_usertree = UserTree.objects.get(id=request.user.id)
            except UserTree.DoesNotExist:
                return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

            if no_initiator_data.claimed_by != current_usertree and not request.user.is_superuser:
                return Response({"error": "You can only mark users you've claimed as spam"}, status=status.HTTP_403_FORBIDDEN)

            no_initiator_data.verification_status = "spam"
            no_initiator_data.save()

            return Response({"message": "User marked as spam successfully"}, status=status.HTTP_200_OK)
        
# class RejectPendingUser(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#     permission_classes = [IsAuthenticated, IsSuperUser]

#     def post(self, request, user_id):
#         with transaction.atomic():
#             pending_user = get_object_or_404(
#                 PendingUser.objects.select_for_update(),
#                 id=user_id,
#                 initiator_id__isnull=True
#             )
#             no_initiator_data = getattr(pending_user, 'no_initiator_data', None)
            
#             try:
#                 current_usertree = UserTree.objects.get(id=request.user.id)
#             except UserTree.DoesNotExist:
#                 return Response({"error": "UserTree entry not found for current user"}, status=status.HTTP_404_NOT_FOUND)

#             # Check if claimed by this user (or allow superuser to reject any)
#             if no_initiator_data and no_initiator_data.claimed_by != current_usertree and not request.user.is_superuser:
#                 return Response({"error": "You can only reject users you've claimed"}, status=status.HTTP_403_FORBIDDEN)

#             # Get rejection reason from request
#             rejection_reason = request.data.get('rejection_reason', '')

#             try:
#                 # Create rejected user record
#                 rejected_user = RejectedPendingUser.objects.create(
#                     gmail=pending_user.gmail,
#                     first_name=pending_user.first_name,
#                     last_name=pending_user.last_name,
#                     profile_picture=pending_user.profile_picture.url if pending_user.profile_picture else None,
#                     date_of_birth=pending_user.date_of_birth,
#                     gender=pending_user.gender,
#                     country_id=pending_user.country.id if pending_user.country else None,
#                     country_name=pending_user.country.name if pending_user.country else None,
#                     state_id=pending_user.state.id if pending_user.state else None,
#                     state_name=pending_user.state.name if pending_user.state else None,
#                     district_id=pending_user.district.id if pending_user.district else None,
#                     district_name=pending_user.district.name if pending_user.district else None,
#                     subdistrict_id=pending_user.subdistrict.id if pending_user.subdistrict else None,
#                     subdistrict_name=pending_user.subdistrict.name if pending_user.subdistrict else None,
#                     village_id=pending_user.village.id if pending_user.village else None,
#                     village_name=pending_user.village.name if pending_user.village else None,
#                     rejected_by=current_usertree,
#                     rejection_reason=rejection_reason,
#                     original_pending_user_id=pending_user.id,
#                     event_type=pending_user.event_type,
#                     is_online=pending_user.is_online
#                 )

#                 # Send rejection notification to user if online
#                 is_online = self.is_user_online(pending_user.gmail)
#                 if is_online:
#                     self.send_rejection_notification(
#                         pending_user.gmail,
#                         rejection_reason
#                     )

#                 # Delete the NoInitiatorUser and PendingUser instances
#                 if no_initiator_data:
#                     no_initiator_data.delete()
#                 pending_user.delete()

#                 return Response({
#                     "message": "User rejected successfully", 
#                     "rejected_user_id": rejected_user.id
#                 }, status=status.HTTP_200_OK)

#             except Exception as e:
#                 return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def is_user_online(self, user_email):
#         """Check if user is currently connected to WebSocket"""
#         return cache.get(f"user_online_{user_email}", False)
        
#     def send_rejection_notification(self, user_email, rejection_reason):
#         """Send WebSocket notification to the user about rejection"""
#         try:
#             channel_layer = get_channel_layer()
#             sanitized_email = re.sub(r'[^a-zA-Z0-9]', '_', user_email)
#             group_name = f"waiting_{sanitized_email}"
            
#             message = {
#                 "type": "admin_rejection",
#                 "status": "rejected",
#                 "message": "❌ Your application has been rejected by our team.",
#                 "rejection_reason": rejection_reason or "No reason provided"
#             }
            
#             async_to_sync(channel_layer.group_send)(
#                 group_name,
#                 {
#                     "type": "admin_rejection_message",
#                     "message": message
#                 }
#             )
#             logger.info(f"Rejection notification sent to {user_email}")
#         except Exception as e:
#             logger.error(f"Failed to send rejection WebSocket notification: {str(e)}")