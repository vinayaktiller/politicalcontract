# import logging
# from django.http import JsonResponse
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from prometheus_client import Counter
# from .services import get_id_token_with_code_method_1
# from .utils import UserCheck, get_tokens_for_user
# from .serializers import LoginResponseSerializer
# from ..models import UserTree  # Add this import


# # Configure logging
# logger = logging.getLogger(__name__)

# # Prometheus metric to count login attempts
# login_attempts = Counter('login_attempts', 'Total number of login attempts', ['user_type'])

# class LoginWithGoogle(APIView):
#     """
#     API view for handling Google OAuth login.

#     This class-based view processes the OAuth `code`, fetches the ID token, 
#     and determines the user's type before responding accordingly.

#     Attributes:
#         - request: The HTTP request containing authentication data.
#     """

#     def post(self, request):
#         """
#         Handle POST request for Google login.

#         Args:
#             request (Request): HTTP request containing OAuth code.

#         Returns:
#             Response: JSON response with user details and tokens (if applicable).
#         """

#         if 'code' in request.data.keys():
#             code = request.data['code']
#             id_token = get_id_token_with_code_method_1(code)
#             user_email = id_token.get('email')
            
#             user_type, user = UserCheck(user_email)
#             logger.info(f"User type detected: {user_type}, Email: {user_email}")
#             login_attempts.labels(user_type=user_type).inc()

#             response_data = {"user_type": user_type, "user_email": user_email}
            
#             if user_type == 'olduser':
#                 # Fetch name and profile picture from UserTree
#                 try:
#                     user_tree = UserTree.objects.get(id=user.id)
#                     name = user_tree.name
#                     profile_pic = user_tree.profilepic.url if user_tree.profilepic else None
#                 except UserTree.DoesNotExist:
#                     name = None
#                     profile_pic = None
#                     logger.warning(f"UserTree not found for user ID: {user.id}")

#                 # Build absolute URL for profile picture
#                 profile_pic_url = request.build_absolute_uri(profile_pic) if profile_pic else None

#                 response_data.update({
#                     "tokens": get_tokens_for_user(user),
#                     "user_id": user.id,
#                     "name": name,
#                     "profile_pic": profile_pic_url  # Add to response
#                 })
                
#             serializer = LoginResponseSerializer(data=response_data)
#             serializer.is_valid(raise_exception=True)
#             return Response(serializer.data)

#         logger.warning("Invalid request: 'code' parameter missing")
#         return Response(status=status.HTTP_400_BAD_REQUEST)
# login/views.py

import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from prometheus_client import Counter
from .services import get_id_token_with_code_method_1
from .utils import UserCheck, get_tokens_for_user
from .serializers import LoginResponseSerializer
from ..models import UserTree
from django.conf import settings

logger = logging.getLogger(__name__)

login_attempts = Counter('login_attempts', 'Total number of login attempts', ['user_type'])

class LoginWithGoogle(APIView):
    def post(self, request):
        if 'code' not in request.data:
            logger.warning("Invalid request: 'code' parameter missing")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        code = request.data['code']
        id_token = get_id_token_with_code_method_1(code)
        user_email = id_token.get('email')
        user_type, user = UserCheck(user_email)
        logger.info(f"User type detected: {user_type}, Email: {user_email}")
        login_attempts.labels(user_type=user_type).inc()

        response_data = {"user_type": user_type, "user_email": user_email}
        
        # Only olduser gets tokens and cookies
        if user_type == 'olduser':
            try:
                user_tree = UserTree.objects.get(id=user.id)
                name = user_tree.name
                profile_pic = user_tree.profilepic.url if user_tree.profilepic else None
            except UserTree.DoesNotExist:
                name = None
                profile_pic = None
                logger.warning(f"UserTree not found for user ID: {user.id}")
            profile_pic_url = request.build_absolute_uri(profile_pic) if profile_pic else None

            tokens = get_tokens_for_user(user)
            response_data.update({
                "user_id": user.id,
                "name": name,
                "profile_pic": profile_pic_url
            })

            serializer = LoginResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            response = Response(serializer.data)

            # Set the cookie domain depending on debug mode for development vs production
            cookie_domain = None
            if settings.DEBUG:
                cookie_domain = None  # Adjust if needed for your dev local domain

            # Set tokens as HttpOnly, Secure cookies
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                httponly=True,
                secure=not settings.DEBUG,  # Use secure cookies only in production
                domain=cookie_domain,
                samesite="Lax",
                # max_age=60 * 60,  # 1 hour
                max_age = 60,  # 1 minute

                path="/"
            )
            response.set_cookie(
                key='refresh_token',
                value=tokens['refresh'],
                httponly=True,
                secure=not settings.DEBUG,
                domain=cookie_domain,
                samesite="Lax",
                max_age=60 * 60 * 24 * 7,  # 1 week
                path="/"
            )
            return response

        # pendinguser or newuser logic (no tokens or cookies)
        serializer = LoginResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
    
    
