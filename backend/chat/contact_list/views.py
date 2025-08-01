# chat/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from users.models import Circle, UserTree
from ..models import Conversation
from .serializers import ContactSerializer
from users.models import Petitioner
from django.utils import timezone

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contact_list(request):
    current_user = request.user
    # Get connections from Circle
    circles = Circle.objects.filter(
        Q(userid=current_user.id) | Q(otherperson=current_user.id)
    )
    
    # Extract unique connection IDs
    connection_ids = set()
    for circle in circles:
        if circle.userid == current_user.id:
            connection_ids.add(circle.otherperson)
        else:
            connection_ids.add(circle.userid)
    
    # Remove current user and None values
    connection_ids = {cid for cid in connection_ids if cid and cid != current_user.id}
    
    # Get user details and existing conversations
    contacts = []
    for user_id in connection_ids:
        try:
            # Get Petitioner and UserTree details
            petitioner = Petitioner.objects.get(id=user_id)
            user_tree = UserTree.objects.get(id=user_id)
            
            # Check for existing conversation
            conversation = Conversation.objects.filter(
                (Q(participant1=current_user.id) & Q(participant2=user_id)) |
                (Q(participant2=current_user.id) & Q(participant1=user_id))
            ).first()
            
            contacts.append({
                'id': user_id,
                'petitioner': petitioner,
                'user_tree': user_tree,
                'conversation_id': conversation.id if conversation else None
            })
        except (Petitioner.DoesNotExist, UserTree.DoesNotExist):
            continue
    
    serializer = ContactSerializer(contacts, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request, contact_id):
    current_user = request.user
    try:
        # Get both users with date_joined
        user1 = current_user
        user2 = Petitioner.objects.get(id=contact_id)
        
        # Determine participant order by date_joined
        if user1.date_joined <= user2.date_joined:
            participant1, participant2 = user1, user2
        else:
            participant1, participant2 = user2, user1
        
        # Create or get conversation
        conversation, created = Conversation.objects.get_or_create(
            participant1=participant1,
            participant2=participant2,
            defaults={
                'last_active': timezone.now()
            }
        )
        
        return Response({
            'conversation_id': conversation.id,
            'created': created
        })
        
    except Petitioner.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)