from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from ..models import Question
from .serializers import QuestionSerializer
from users.login.authentication import CookieJWTAuthentication


class QuestionPagination(PageNumberPagination):
    page_size = 5  # 5 questions per page
    page_size_query_param = 'page_size'  # optional override via query param
    max_page_size = 20


class QuestionListAPI(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QuestionPagination

    def get(self, request):
        # Filter to approved questions only, ordered by rank and created_at
        queryset = Question.objects.filter(is_approved=True).order_by('rank', 'created_at')

        paginator = self.pagination_class()
        paged_qs = paginator.paginate_queryset(queryset, request, view=self)

        serializer = QuestionSerializer(paged_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
