from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from .serializers import GroupSerializer
from ...models.groups import Group
from users.models.usertree import UserTree

class UserGroupsAPIView(APIView):
    def get(self, request):
        try:
            print(f"Requesting User ID: {request.user.id}")  # Debugging
            user_tree = UserTree.objects.get(id=request.user.id)
            print(f"Retrieved UserTree Instance: {user_tree}")  # Debugging
        except UserTree.DoesNotExist:
            return Response(
                {"error": "User profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filter groups where user is founder, speaker, member, or agent
        groups = Group.objects.filter(
            Q(founder=user_tree.id) |  # Ensure it's an instance, not just an ID
            Q(speakers__contains=[user_tree.id]) |
            Q(members__contains=[user_tree.id]) |
            Q(outside_agents__contains=[user_tree.id])
        ).distinct()

        print(f"Filtered Groups: {groups}")  # Debugging
        
        # Fetch user instances for serialization
        user_ids = {group.founder for group in groups}
        for group in groups:
            user_ids.update(group.speakers)

        users = UserTree.objects.filter(id__in=user_ids)
        user_map = {user.id: user for user in users}
        
        print(f"User Map: {user_map}")  # Debugging

        # Serialize groups with context
        context = {'request': request, 'user_map': user_map}
        serializer = GroupSerializer(groups, many=True, context=context)
        serialized_data = serializer.data
        
        print(f"Serialized Data: {serialized_data}")  # Debugging
        
        upcoming_groups = [g for g in serialized_data if not g.get('members_count')]
        old_groups = [g for g in serialized_data if g.get('members_count')]
        
        return Response({
            "upcoming_groups": upcoming_groups,
            "old_groups": old_groups
        })
