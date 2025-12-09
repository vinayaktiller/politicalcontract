from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_list_or_404
from ..models import Milestone
from .serializers import MilestoneSerializer

class UserMilestonesAPIView(APIView):
    """
    API endpoint to list milestones for a given user ID.
    API RULE: Never update fields, only return data.
    """

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # API RULE: Only include milestones where delivered=True AND completed=True
        milestones = Milestone.objects.filter(
            user_id=user_id,
            delivered=True,
            completed=True
        )

        if not milestones.exists():
            return Response({'message': 'No milestones found for this user.'}, status=status.HTTP_200_OK)

        # API RULE: DO NOT UPDATE ANY FIELDS
        serializer = MilestoneSerializer(milestones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkMilestoneCompletedAPIView(APIView):
    """
    NOTIFICATION BAR CLICK API: Mark milestone as completed when user clicks notification.
    Expects milestone_id in request body.
    """
    
    def post(self, request, *args, **kwargs):
        milestone_id = request.data.get('milestone_id')
        
        if not milestone_id:
            return Response(
                {'error': 'milestone_id is required in request body.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            milestone = Milestone.objects.get(id=milestone_id, user_id=request.user.id)
            
            # NOTIFICATION BAR CLICK RULE: Only update completed, not delivered
            milestone.mark_as_completed()
            
            return Response(
                {'success': True, 'message': 'Milestone marked as completed'},
                status=status.HTTP_200_OK
            )
            
        except Milestone.DoesNotExist:
            return Response(
                {'error': 'Milestone not found or does not belong to user'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )