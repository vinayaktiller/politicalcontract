# views.py
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import UserTree
from users.login.authentication import CookieJWTAuthentication 

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication])
@permission_classes([IsAuthenticated])
def validate_users(request):
    user_ids = request.data.get('user_ids', [])
    valid_users = []
    
    for user_id in user_ids:
        try:
            user = UserTree.objects.get(id=user_id)
            valid_users.append({
                'id': user.id,
                'name': user.name,
                'profile_pic': request.build_absolute_uri(user.profilepic.url) if user.profilepic else None
            })
        except UserTree.DoesNotExist:
            continue
    
    return Response({'valid_users': valid_users})