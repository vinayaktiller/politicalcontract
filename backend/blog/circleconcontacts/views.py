from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from users.models import Circle, UserTree
from django.contrib.auth import get_user_model
from users.login.authentication import CookieJWTAuthentication


User = get_user_model()

class CircleContactsView(generics.GenericAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get current user's UserTree by matching User.id with UserTree.id
        try:
            self_contact = UserTree.objects.get(id=user.id)
        except UserTree.DoesNotExist:
            self_contact = None
        
        # Get all circles for current user
        circles = Circle.objects.filter(userid=user.id)
        
        # Get all contact IDs from circle.otherperson
        contact_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Fetch matching UserTree contacts
        contacts = UserTree.objects.filter(id__in=contact_ids)
        
        response_data = []

        # Add self contact
        if self_contact:
            response_data.append({
                'id': self_contact.id,
                'name': self_contact.name,
                'profile_pic': self.get_profile_pic_url(request, self_contact),
                'relation': 'Your Journey'
            })
        
        # Add other contacts with relation
        for contact in contacts:
            circle = circles.filter(otherperson=contact.id).first()
            relation = circle.onlinerelation if circle else "Connection"
            
            response_data.append({
                'id': contact.id,
                'name': contact.name,
                'profile_pic': self.get_profile_pic_url(request, contact),
                'relation': relation.replace('_', ' ').title()
            })
        
        return Response(response_data)
    
    def get_profile_pic_url(self, request, user_tree):
        if user_tree.profilepic:
            return request.build_absolute_uri(user_tree.profilepic.url)
        return None
