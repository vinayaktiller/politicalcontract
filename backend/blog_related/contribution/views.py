# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ContributionCreateSerializer, ContributionConflictSerializer, ContributionDetailSerializer
from ..models import Contribution, ContributionConflict
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from users.models import UserTree  # Import UserTree model

class ContributionCreateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        link = request.data.get('link')
        
        if link:
            try:
                existing_contribution = Contribution.objects.get(link=link)
                
                # If contribution exists and has an owner, it's already claimed
                if existing_contribution.owner is not None:
                    # Get owner details from UserTree
                    owner_details = {}
                    try:
                        owner_user = UserTree.objects.get(id=existing_contribution.owner)
                        owner_details = {
                            'id': owner_user.id,
                            'name': owner_user.name,
                            'profile_pic': request.build_absolute_uri(owner_user.profilepic.url) if owner_user.profilepic else None
                        }
                    except UserTree.DoesNotExist:
                        owner_details = {
                            'id': existing_contribution.owner,
                            'name': f'User #{existing_contribution.owner}',
                            'profile_pic': None
                        }
                    
                    # Return the existing contribution details for conflict reporting
                    contribution_data = ContributionDetailSerializer(existing_contribution).data
                    contribution_data['owner_details'] = owner_details
                    
                    return Response(
                        {
                            'error': 'This URL has already been claimed by another user.',
                            'existing_contribution': contribution_data,
                            'conflict': True,
                            'disputed_data': {  # Include the disputed data in the response
                                'title': request.data.get('title'),
                                'description': request.data.get('discription'),
                                'teammembers': request.data.get('teammembers', [])
                            }
                        },
                        status=status.HTTP_409_CONFLICT
                    )
                
                # If it's an orphan contribution, update it
                serializer = ContributionCreateSerializer(
                    existing_contribution, 
                    data=request.data,
                    partial=True
                )
                
                if serializer.is_valid():
                    contribution = serializer.save(owner=request.user.id)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            except Contribution.DoesNotExist:
                # No contribution exists with this link, create a new one
                pass
        
        # Create a new contribution
        serializer = ContributionCreateSerializer(data=request.data)
        if serializer.is_valid():
            contribution = serializer.save(owner=request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ContributionConflictView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ContributionConflictSerializer(data=request.data)
        
        if serializer.is_valid():
            # Ensure the user is the one reporting the conflict
            conflict = serializer.save(
                reported_by=request.user.id,
                status='pending'
            )
            return Response(ContributionConflictSerializer(conflict).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from rest_framework import generics
from django.db.models import Q

class UserContributionsView(generics.ListAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ContributionDetailSerializer
    
    def get_queryset(self):
        user_id = self.request.user.id
        # Get contributions where user is owner OR team member
        return Contribution.objects.filter(
            Q(owner=user_id) | Q(teammembers__contains=[user_id])
        ).order_by('-created_at')