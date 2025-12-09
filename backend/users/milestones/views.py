from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_list_or_404
from ..models import Milestone
from .serializers import MilestoneSerializer
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


# Logger for this module
logger = logging.getLogger(__name__)

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


@method_decorator(csrf_exempt, name='dispatch')  # TEMP for debugging only
class MarkMilestoneCompletedAPIView(APIView):
    """
    Diagnostic: logs arrival of all methods. Keep csrf_exempt only for debugging.
    """

    def options(self, request, *args, **kwargs):
        logger.info("OPTIONS received for %s by user=%s", request.path, getattr(request.user, 'id', None))
        return Response(status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        logger.info("GET received for %s (method not allowed for marking complete)", request.path)
        return Response({'error': 'GET not supported on this endpoint'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        logger.info("POST received for %s: user=%s body=%s", request.path, getattr(request.user, 'id', None), request.data)
        milestone_id = request.data.get('milestone_id')
        if not milestone_id:
            logger.debug("Missing milestone_id")
            return Response({'error': 'milestone_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        player=request.user.id
        logger.info(" player %s Marking milestone %s completed for user %s", milestone_id, player)

        # user_id = getattr(request.user, 'id', None)
        user_id = request.user.id
        if user_id is None:
            logger.debug("Unauthenticated request")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            milestone = Milestone.objects.get(id=milestone_id, user_id=user_id)
            milestone.mark_as_completed()
            logger.info("Marked milestone %s completed for user %s", milestone_id, user_id)
            return Response({'success': True}, status=status.HTTP_200_OK)
        except Milestone.DoesNotExist:
            logger.warning("Milestone not found id=%s user=%s", milestone_id, user_id)
            return Response({'error': 'Milestone not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Unexpected error marking milestone completed: %s", e)
            return Response({'error': 'internal error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)