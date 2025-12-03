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
        target_user_id = request.query_params.get('user_id', request.user.id)
        
        if str(target_user_id) != str(request.user.id):
            return Response(
                {'error': 'You can only view your own contributions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        search_query = request.query_params.get('search', '')
        type_filter = request.query_params.get('type', '')
        
        contributions = Contribution.objects.filter(owner=target_user_id)
        
        if search_query:
            contributions = contributions.filter(
                Q(title__icontains=search_query) |
                Q(discription__icontains=search_query) |
                Q(link__icontains=search_query)
            )
        
        if type_filter:
            contributions = contributions.filter(type=type_filter)
        
        contributions = contributions.order_by('-created_at')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(contributions, request)
        
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
