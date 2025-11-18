import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import UserTree
from .utils import get_tokens_for_user
from .serializers import LandingResponseSerializer
from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()

class LandingPageAuth(APIView):
    """
    Handle authentication for users arriving at landing page after verification
    This issues tokens similar to login flow but uses email from storage
    """
    
    def post(self, request):
        if 'user_email' not in request.data:
            logger.warning("Invalid request: 'user_email' parameter missing")
            return Response(
                {"error": "user_email is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user_email = request.data['user_email']
        logger.info(f"Landing page auth attempt for email: {user_email}")

        try:
            # Find user by email
            user = User.objects.get(email=user_email)
            
            # Get user profile data from UserTree
            try:
                user_tree = UserTree.objects.get(id=user.id)
                name = user_tree.name
                profile_pic = user_tree.profilepic.url if user_tree.profilepic else None
            except UserTree.DoesNotExist:
                name = None
                profile_pic = None
                logger.warning(f"UserTree not found for user ID: {user.id}")

            # Build profile pic URL
            profile_pic_url = request.build_absolute_uri(profile_pic) if profile_pic else None

            # Generate tokens
            tokens = get_tokens_for_user(user)

            # Prepare response data
            response_data = {
                "user_type": "olduser",  # Always set to olduser since they're verified
                "user_email": user_email,
                "user_id": user.id,
                "name": name,
                "profile_pic": profile_pic_url,
                "message": "Successfully authenticated for landing page"
            }

            serializer = LandingResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            response = Response(serializer.data)

            # Set tokens as HttpOnly cookies (same as login flow)
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                httponly=True,
                secure=True,
                domain='.centralus-01.azurewebsites.net',
                samesite='None',
                max_age=60,
                path='/',
            )

            response.set_cookie(
                key='refresh_token',
                value=tokens['refresh'],
                httponly=True,
                secure=True,
                domain='.centralus-01.azurewebsites.net',
                samesite='None',
                max_age=60 * 60 * 24 * 7,
                path='/',
            )

            logger.info(f"Successfully issued tokens for landing page user: {user_email}")
            return response

        except User.DoesNotExist:
            logger.error(f"User not found for email: {user_email}")
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in landing page auth: {str(e)}")
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )