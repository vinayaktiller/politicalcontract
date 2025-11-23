# users/refresh/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CookieTokenRefreshView(APIView):
    def post(self, request):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')
        logger.debug(f"Received refresh token from cookie: {refresh_token[:10]}... (truncated)" if refresh_token else "No refresh token found in cookie")
        
        if not refresh_token:
            logger.warning("Refresh token not found in cookie")
            return Response(
                {"error": "Refresh token not found"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create a RefreshToken instance from the provided token
            refresh = RefreshToken(refresh_token)
            
            # Generate new access token
            access_token = str(refresh.access_token)
            
            # Create response
            response = Response({"message": "Token refreshed successfully"})
            
            # ===== IMPROVED DOMAIN CONFIGURATION =====
            # Get the current request's domain
            current_domain = request.get_host()
            
            # Remove port if present
            if ':' in current_domain:
                current_domain = current_domain.split(':')[0]
            
            logger.info(f"Token refresh - Current domain: {current_domain}")
            
            # Determine cookie domain based on environment
            if 'centralus-01.azurewebsites.net' in current_domain:
                # For Azure deployment - use the common domain root
                cookie_domain = '.centralus-01.azurewebsites.net'
                secure_flag = True
                same_site = 'None'
                logger.info(f"Using Azure domain configuration: {cookie_domain}")
            else:
                # For local development or same domain
                cookie_domain = None
                secure_flag = not settings.DEBUG  # False in development, True in production
                same_site = 'Lax' if settings.DEBUG else 'None'
                logger.info(f"Using local/same-domain configuration: domain=None, secure={secure_flag}, samesite={same_site}")
            
            # Set the new access token in cookie
            cookie_kwargs = {
                'key': 'access_token',
                'value': access_token,
                'httponly': True,
                'secure': secure_flag,
                'samesite': same_site,
                'max_age': 60,  # 1 minute (matches your login view)
                'path': '/',
            }
            
            # Only add domain parameter if we have a specific domain to set
            if cookie_domain:
                cookie_kwargs['domain'] = cookie_domain
            
            response.set_cookie(**cookie_kwargs)
            
            logger.info(f"Access token refreshed and set in cookie with domain: {cookie_domain}")
            return response
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response(
                {"error": "Invalid or expired refresh token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


# # users/refresh/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.conf import settings
# import logging

# logger = logging.getLogger(__name__)

# class CookieTokenRefreshView(APIView):
#     def post(self, request):
#         # Get refresh token from cookie
#         refresh_token = request.COOKIES.get('refresh_token')
#         logger.debug(f"Received refresh token from cookie: {refresh_token[:10]}... (truncated)" if refresh_token else "No refresh token found in cookie")
        
#         if not refresh_token:
#             logger.warning("Refresh token not found in cookie")
#             return Response(
#                 {"error": "Refresh token not found"}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         try:
#             # Create a RefreshToken instance from the provided token
#             refresh = RefreshToken(refresh_token)
            
#             # Generate new access token
#             access_token = str(refresh.access_token)
            
#             # Create response
#             response = Response({"message": "Token refreshed successfully"})
            
#             # # Set the new access token in cookie
#             # response.set_cookie(
#             #     key='access_token',
#             #     value=access_token,
#             #     httponly=True,
#             #     secure=not settings.DEBUG,
#             #     samesite='Lax',
#             #     max_age=60 * 60,  # 1 hour
#             #     path='/'
#             # )
            
#             #seting form deployed backend to frontend
#             response.set_cookie(
#                 key='access_token',
#                 value=access_token,
#                 httponly=True,
#                 secure=True,  # Must be True for HTTPS 
#                 domain='.centralus-01.azurewebsites.net',  # Use your backend domain root
#                 samesite='None',  # Allows cross-site requests, requires secure=True
#                 max_age=60,  # Adjust as per your token expiry plan
#                 path='/',
#             )
#             logger.info("Token refreshed successfully")
#             return response
            
#         except Exception as e:
#             logger.error(f"Token refresh failed: {str(e)}")
#             return Response(
#                 {"error": "Invalid or expired refresh token"}, 
#                 status=status.HTTP_401_UNAUTHORIZED
#             )