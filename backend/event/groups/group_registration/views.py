from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import GroupRegistrationSerializer

class GroupRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = GroupRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            group = serializer.save()
            return Response({
                'status': 'success',
                'group_id': group.id,
                'message': 'Group created successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)