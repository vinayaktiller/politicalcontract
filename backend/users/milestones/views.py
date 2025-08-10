from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_list_or_404
from ..models import Milestone
from .serializers import MilestoneSerializer

class UserMilestonesAPIView(APIView):
    """
    API endpoint to list milestones for a given user ID.
    Marks all returned milestones with delivered=True.
    """

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get milestones for user or empty list if none
        milestones = Milestone.objects.filter(user_id=user_id)

        if not milestones.exists():
            return Response({'message': 'No milestones found for this user.'}, status=status.HTTP_200_OK)

        # Update delivered=True for all milestones with delivered=False
        undelivered = milestones.filter(delivered=False)
        undelivered.update(delivered=True)

        serializer = MilestoneSerializer(milestones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
