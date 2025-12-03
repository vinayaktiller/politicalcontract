from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ...models import Contribution
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from blog.models import MicroConsumption, ShortEssayConsumption, ArticleConsumption

@api_view(['GET'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_or_create_contribution_by_link(request):
    link = request.GET.get('link')
    if not link:
        return Response({'error': 'Link parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        contribution = Contribution.objects.get(link=link)
        return Response({
            'id': str(contribution.id),
            'title': contribution.title,
            'description': contribution.discription,
            'type': contribution.type,
        })
    except Contribution.DoesNotExist:
        contribution = Contribution.objects.create(link=link, byconsumer=request.user.id)
        return Response({
            'id': str(contribution.id),
            'title': 'orphan contribution',
            'description': 'not claimed yet',
            'type': 'none',
        }, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_contribution(request, contribution_id):
    try:
        contribution = Contribution.objects.get(id=contribution_id, byconsumer=request.user.id)
        
        if MicroConsumption.objects.filter(contribution=contribution.id).exists():
            return Response(
                {'error': 'Cannot delete contribution that is used in MicroConsumption'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if ShortEssayConsumption.objects.filter(contribution=contribution.id).exists():
            return Response(
                {'error': 'Cannot delete contribution that is used in ShortEssayConsumption'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if ArticleConsumption.objects.filter(contribution=contribution.id).exists():
            return Response(
                {'error': 'Cannot delete contribution that is used in ArticleConsumption'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contribution.delete()
        return Response({'status': 'deleted'}, status=status.HTTP_200_OK)
    
    except Contribution.DoesNotExist:
        return Response({'error': 'Contribution not found'}, status=status.HTTP_404_NOT_FOUND)