# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from ...models.groups import Group 
from ...models.group_speaker_invitation_notifiation import GroupSpeakerInvitationNotification
from users.models.petitioners import Petitioner
from .serializers import GroupSerializer, UserTreeSerializer
from users.models.usertree import UserTree
from django.db.models import Prefetch
from users.login.authentication import CookieJWTAuthentication 
import logging

logger = logging.getLogger(__name__)

class GroupDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)
            
            # Prefetch related users
            user_ids = [group.founder] + group.speakers + group.pending_speakers
            users = UserTree.objects.filter(id__in=user_ids)
            user_map = {user.id: user for user in users}
            
            # Serialize with user data
            serializer = GroupSerializer(group, context={
                'request': request,
                'user_map': user_map
            })
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ObjectDoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class VerifySpeakerView(APIView):
    """Verifies if a user ID should be considered for addition (not already in speakers or pending speakers)."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        user_id = request.data.get("user_id")
        print(f"Received user_id: {user_id} for group_id: {group_id}")
        
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = int(user_id)
            group = Group.objects.get(id=group_id)
            
            # Ensure user is not the founder
            if user_id == group.founder:
                return Response({"error": "Founder cannot be added as a speaker"}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure user is NOT already in speakers or pending speakers
            if user_id in group.speakers or user_id in group.pending_speakers:
                return Response({"error": "User is already in speakers or pending speakers"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Retrieve and serialize user tree data, passing the request context
            user_tree = UserTree.objects.get(id=user_id)
            serialized_user = UserTreeSerializer(user_tree, context={"request": request}).data
            
            return Response({"user": serialized_user}, status=status.HTTP_200_OK)
        
        except (ValueError, TypeError):
            return Response({"error": "Invalid user ID format"}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"error": "Group or UserTree not found"}, status=status.HTTP_404_NOT_FOUND)

class AddPendingSpeakerView(APIView):
    """Adds a user to the pending speakers list upon frontend confirmation."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        user_id = request.data.get("user_id")
        print(f"Received user_id: {user_id} (type: {type(user_id)}) for group_id: {group_id}")

        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = int(user_id)  # This shouldn't fail
            group = Group.objects.get(id=group_id)

            print(f"Group pending_speakers before update: {group.pending_speakers} (type: {type(group.pending_speakers)})")

            # Ensure pending_speakers is a list
            if not isinstance(group.pending_speakers, list):
                return Response({"error": "Group pending_speakers must be a list"}, status=status.HTTP_400_BAD_REQUEST)

            # Append user to pending speakers and save
            group.pending_speakers.append(user_id)
            group.save()

            print(f"Group pending_speakers after update: {group.pending_speakers}")

            try:
                speaker = Petitioner.objects.get(id=user_id)
                GroupSpeakerInvitationNotification.objects.create(
                    group=group,
                    speaker=speaker
                )
            except Petitioner.DoesNotExist:
                logger.error(f"User {user_id} not found when creating speaker invitation")

            return Response({"success": f"User {user_id} added to pending speakers"}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

class UploadGroupProfilePictureView(APIView):
    """Handles group profile picture upload - only founder can upload"""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)
            
            # Check if the current user is the founder
            if request.user.id != group.founder:
                return Response(
                    {"error": "Only the group founder can upload profile picture"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if profile picture is in request
            if 'profile_pic' not in request.FILES:
                return Response(
                    {"error": "Profile picture file is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            profile_pic_file = request.FILES['profile_pic']
            
            # Validate file size (optional - 5MB limit)
            if profile_pic_file.size > 5 * 1024 * 1024:
                return Response(
                    {"error": "File size too large. Maximum size is 5MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the profile picture
            group.profile_pic = profile_pic_file
            group.save()
            
            # Return the updated group data
            user_ids = [group.founder] + group.speakers + group.pending_speakers
            users = UserTree.objects.filter(id__in=user_ids)
            user_map = {user.id: user for user in users}
            
            serializer = GroupSerializer(group, context={
                'request': request,
                'user_map': user_map
            })
            
            return Response({
                "success": "Profile picture uploaded successfully",
                "group": serializer.data
            }, status=status.HTTP_200_OK)
            
        except ObjectDoesNotExist:
            return Response(
                {"error": "Group not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error uploading profile picture: {str(e)}")
            return Response(
                {"error": "Failed to upload profile picture"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )