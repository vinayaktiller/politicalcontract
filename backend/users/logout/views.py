# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from ..models.petitioners import Petitioner  # Import your model

# class LogoutView(APIView):
#     def post(self, request):
#         user_id = request.data.get('user_id')

#         try:
#             petitioner = Petitioner.objects.get(id=user_id)
#             petitioner.is_online = False
#             petitioner.save()
#             return Response({"message": "User logged out successfully"}, status=status.HTTP_200_OK)
#         except Petitioner.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models.petitioners import Petitioner  # Import your model

class LogoutView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')

        try:
            petitioner = Petitioner.objects.get(id=user_id)
            petitioner.is_online = False
            petitioner.save()

            response = Response(
                {"message": "User logged out successfully"},
                status=status.HTTP_200_OK
            )
            # Delete cookies on client
            response.delete_cookie(
                'access_token',
                domain='.centralus-01.azurewebsites.net',
                path='/'
            )
            response.delete_cookie(
                'refresh_token',
                domain='.centralus-01.azurewebsites.net',
                path='/'
            )
            return response

        except Petitioner.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
