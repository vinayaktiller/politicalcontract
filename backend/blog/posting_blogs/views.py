from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BlogCreateSerializer


class BlogCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BlogCreateSerializer(data=request.data)
        if serializer.is_valid():
            blog = serializer.save()
            return Response({
                'id': str(blog.id),
                'message': 'Blog created successfully',
                'type': request.data.get('type'),
                'content_type': request.data.get('content_type')
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
