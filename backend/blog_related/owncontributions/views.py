from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .serializers import ContributionListSerializer
from ..models import Contribution
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class ContributionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ContributionListView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = ContributionPagination
    
    def get(self, request):
        # Get the target user ID from query params, default to current user
        target_user_id = request.query_params.get('user_id', request.user.id)
        
        # Check if the current user has permission to view the target user's contributions
        # For now, we'll allow users to view their own contributions only
        # You can modify this logic based on your requirements
        if str(target_user_id) != str(request.user.id):
            return Response(
                {'error': 'You can only view your own contributions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get filter parameters
        search_query = request.query_params.get('search', '')
        
        # Build the queryset
        contributions = Contribution.objects.filter(owner=target_user_id)
        
        # Apply search filter if provided
        if search_query:
            contributions = contributions.filter(
                Q(title__icontains=search_query) |
                Q(discription__icontains=search_query) |
                Q(link__icontains=search_query)
            )
        
        # Order by creation date (newest first)
        contributions = contributions.order_by('-created_at')
        
        # Paginate the results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(contributions, request)
        
        # Serialize the data
        serializer = ContributionListSerializer(
            page, 
            many=True, 
            context={'request': request}
        )
        
        return paginator.get_paginated_response(serializer.data)

class ContributionDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, contribution_id):
        try:
            contribution = Contribution.objects.get(id=contribution_id)
            
            # Check if the user has permission to view this contribution
            if str(contribution.owner) != str(request.user.id):
                return Response(
                    {'error': 'You do not have permission to view this contribution'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ContributionListSerializer(
                contribution, 
                context={'request': request}
            )
            return Response(serializer.data)
        except Contribution.DoesNotExist:
            return Response(
                {'error': 'Contribution not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class ContributionDeleteView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, contribution_id):
        try:
            contribution = Contribution.objects.get(id=contribution_id)
            
            # Check if the user has permission to delete this contribution
            if str(contribution.owner) != str(request.user.id):
                return Response(
                    {'error': 'You do not have permission to delete this contribution'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            contribution.delete()
            return Response(
                {'message': 'Contribution deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Contribution.DoesNotExist:
            return Response(
                {'error': 'Contribution not found'},
                status=status.HTTP_404_NOT_FOUND
            )