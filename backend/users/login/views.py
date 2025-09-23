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

            # # Set tokens as HttpOnly, Secure cookies
            # response.set_cookie(
            #     key='access_token',
            #     value=tokens['access'],
            #     httponly=True,
            #     secure=not settings.DEBUG,  # Use secure cookies only in production
            #     domain=cookie_domain,
            #     samesite="Lax",
            #     max_age=60,  # 1 minute
            #     path="/"
            # )
            # response.set_cookie(
            #     key='refresh_token',
            #     value=tokens['refresh'],
            #     httponly=True,
            #     secure=not settings.DEBUG,
            #     domain=cookie_domain,
            #     samesite="Lax",
            #     max_age=60 * 60 * 24 * 7,  # 1 week
            #     path="/"
            # )

            # teken cookies settings for Azure deployment and local frontend
            # response.set_cookie(
            #     key='access_token',
            #     value=tokens['access'],
            #     httponly=True,
            #     secure=True,  # Always secure in Azure
            #     samesite="None",  # Allow cross-site cookies
            #     max_age=60,
            #     path="/",
            # )

            # response.set_cookie(
            #     key='refresh_token',
            #     value=tokens['refresh'],
            #     httponly=True,
            #     secure=True,
            #     samesite="None",
            #     max_age=60 * 60 * 24 * 7,
            #     path="/",
            # )

            # Original cookie settings for reference
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                httponly=True,
                secure=True,  # Must be True for HTTPS 
                domain='.centralus-01.azurewebsites.net',  # Use your backend domain root
                samesite='None',  # Allows cross-site requests, requires secure=True
                max_age=60,  # Adjust as per your token expiry plan
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


            return response

        # Special flag for no_initiator users
        elif user_type == 'no_initiator':
            response_data['no_initiator'] = True

        # For pendinguser, no_initiator, newuser - return basic response only
        serializer = LoginResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
