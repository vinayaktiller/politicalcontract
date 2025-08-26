# users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Check if token is in cookie
        raw_token = request.COOKIES.get("access_token")
        
        if raw_token is None:
            logger.debug("No access token found in cookie")
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            logger.debug(f"Authentication successful for user {user.id}")
            return user, validated_token
        except (InvalidToken, AuthenticationFailed) as e:
            logger.warning(f"Token validation failed: {str(e)}")
            # Don't raise exception here, let the view handle it
            return None
    

# import logging
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework import exceptions
# from django.conf import settings

# logger = logging.getLogger(__name__)

# class CookieJWTAuthentication(JWTAuthentication):
#     def authenticate(self, request):
#         logger.debug("Starting authentication using CookieJWTAuthentication")

#         # Try to get token from the Authorization header first
#         header = self.get_header(request)
#         if header is None:
#             # No Authorization header; fallback to cookie
#             cookie_name = getattr(settings, "SIMPLE_JWT", {}).get("AUTH_COOKIE", "access_token")
#             raw_token = request.COOKIES.get(cookie_name)
#             if raw_token is None:
#                 logger.warning(f"Authentication failed: No token found in cookie '{cookie_name}'")
#                 return None
#             else:
#                 logger.debug(f"Token found in cookie '{cookie_name}': {raw_token[:10]}... (truncated)")
#         else:
#             raw_token = self.get_raw_token(header)
#             logger.debug(f"Token found in Authorization header: {raw_token[:10]}... (truncated)")

#         try:
#             validated_token = self.get_validated_token(raw_token)
#             logger.debug("Token successfully validated")
#         except exceptions.AuthenticationFailed as exc:
#             logger.warning(f"Token validation failed: {exc}")
#             return None  # or raise exceptions.AuthenticationFailed if you want strict rejection

#         user = self.get_user(validated_token)
#         if user is None:
#             logger.warning("No user found for validated token")
#         else:
#             logger.debug(f"Authenticated user: {user}")

#         return (user, validated_token)

# import logging
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework import exceptions
# from django.conf import settings

# logger = logging.getLogger(__name__)

# class CookieJWTAuthentication(JWTAuthentication):
#     def authenticate(self, request):
#         logger.debug("Starting authentication using CookieJWTAuthentication")

#         # Check token in Authorization header first (Bearer Token)
#         header = self.get_header(request)
#         logger.debug(f"Authorization header: {header}")
#         if header is not None:
#             raw_token = self.get_raw_token(header)
#             if raw_token:
#                 logger.debug("Token found in Authorization header")
#                 try:
#                     validated_token = self.get_validated_token(raw_token)
#                     user = self.get_user(validated_token)
#                     return (user, validated_token)
#                 except exceptions.AuthenticationFailed as e:
#                     logger.warning(f"Header token validation failed: {e}")

#         # Fallback to token in cookie
#         cookie_name = getattr(settings, "SIMPLE_JWT", {}).get("AUTH_COOKIE", "access_token")
#         raw_token = request.COOKIES.get(cookie_name)

#         if raw_token is None:
#             logger.warning(f"No token found in cookie '{cookie_name}'")
#             # Development fallback: check Authorization header in META
#             if getattr(settings, 'DEBUG', False):
#                 auth_header = request.META.get('HTTP_AUTHORIZATION', '')
#                 if auth_header.startswith('Bearer '):
#                     raw_token = auth_header.split(' ')[1]
#                     logger.debug("Found token in Authorization header (development fallback)")

#             if raw_token is None:
#                 return None

#         try:
#             validated_token = self.get_validated_token(raw_token)
#             user = self.get_user(validated_token)
#             logger.debug(f"Authenticated user via cookie: {user}")
#             return (user, validated_token)
#         except exceptions.AuthenticationFailed as e:
#             logger.warning(f"Token validation failed: {e}")
#             return None
