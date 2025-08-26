# Add this to your views.py
# users/login/TestCookieView.py (or wherever it lives)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from users.login.authentication import CookieJWTAuthentication  # adjust import if path differs


class TestCookieView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Safely get an email-like field
        user_email = getattr(user, "email", None) or getattr(user, "gmail", None) or getattr(user, "username", None)

        return Response({
            "message": "Cookie authentication successful",
            "user_id": getattr(user, "id", None),
            "user_email": user_email
        })
