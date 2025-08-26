# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ...models.groups import Group
from ...models.UserGroupParticipation import UserGroupParticipation
from .serializers import UserGroupSerializer
from users.login.authentication import CookieJWTAuthentication  # Import your authentication class


class UserGroupsAPI(APIView):
    """
    API to get all groups related to the authenticated user
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.user.id
        
        # 1. Find groups where user is the founder
        founder_groups = Group.objects.filter(founder=user_id)
        
        # 2. Find groups from UserGroupParticipation where user is a speaker
        try:
            participation = UserGroupParticipation.objects.get(user_id=user_id)
            speaker_group_ids = participation.groups_as_speaker
            speaker_groups = Group.objects.filter(id__in=speaker_group_ids)
        except UserGroupParticipation.DoesNotExist:
            speaker_groups = Group.objects.none()
        
        # 3. Combine all groups and remove duplicates
        all_groups = (founder_groups | speaker_groups).distinct()
        
        # Serialize the results
        serializer = UserGroupSerializer(all_groups, many=True)
        return Response({"groups": serializer.data})