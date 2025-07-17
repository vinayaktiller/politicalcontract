# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ...models.groups import Group
from users.models.usertree import UserTree
from .serializers import GroupDetailSerializer

class GroupDetailpageView(APIView):
    """
    GET /api/event/group/<group_id>/details/
    """
    def get(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # gather every user‐id we need
        all_user_ids = {group.founder}
        all_user_ids.update(group.speakers)
        all_user_ids.update(group.members)
        all_user_ids.update(group.outside_agents)

        # 🔑 filter on the real PK field, `id`
        users = UserTree.objects.filter(id__in=all_user_ids)
        user_map = {u.id: u for u in users}

        serializer = GroupDetailSerializer(
            group,
            context={'request': request, 'user_map': user_map}
        )
        return Response(serializer.data)

