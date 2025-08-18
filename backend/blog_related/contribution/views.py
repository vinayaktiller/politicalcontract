from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ContributionCreateSerializer

class ContributionCreateView(APIView):
    """
    API endpoint to allow users to create a Contribution (POST only).
    """
    http_method_names = ['post']   # ✅ explicitly only allow POST

    def post(self, request, *args, **kwargs):
        serializer = ContributionCreateSerializer(data=request.data)
        if serializer.is_valid():
            contribution = serializer.save()   # id will auto-generate
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
