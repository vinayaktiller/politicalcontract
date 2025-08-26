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
            
            # Set the new access token in cookie
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=60 * 60,  # 1 hour
                path='/'
            )
            
            logger.info("Token refreshed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response(
                {"error": "Invalid or expired refresh token"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )