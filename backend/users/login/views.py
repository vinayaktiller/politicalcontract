import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from prometheus_client import Counter
from .services import get_id_token_with_code_method_1
from .utils import UserCheck, get_tokens_for_user
from .serializers import LoginResponseSerializer


# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metric to count login attempts
login_attempts = Counter('login_attempts', 'Total number of login attempts', ['user_type'])

class LoginWithGoogle(APIView):
    """
    API view for handling Google OAuth login.

    This class-based view processes the OAuth `code`, fetches the ID token, 
    and determines the user's type before responding accordingly.

    Attributes:
        - request: The HTTP request containing authentication data.
    """

    def post(self, request):
        """
        Handle POST request for Google login.

        Args:
            request (Request): HTTP request containing OAuth code.

        Returns:
            Response: JSON response with user details and tokens (if applicable).
        """

        if 'code' in request.data.keys():
            code = request.data['code']
            
            id_token = get_id_token_with_code_method_1(code)
            user_email = id_token.get('email')

            user_type, user = UserCheck(user_email)
            logger.info(f"User type detected: {user_type}, Email: {user_email}")

            login_attempts.labels(user_type=user_type).inc()

            response_data = {"user_type": user_type, "user_email": user_email}
            

            if user_type == 'olduser':
                
                response_data.update({
                    "tokens": get_tokens_for_user(user),
                    "user_id": user.id
                })
                

            serializer = LoginResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data)

        logger.warning("Invalid request: 'code' parameter missing")
        return Response(status=status.HTTP_400_BAD_REQUEST)
