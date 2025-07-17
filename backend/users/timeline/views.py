from django.core.paginator import EmptyPage, PageNotAnInteger
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from collections import defaultdict

from ..models.usertree import UserTree
from ..models.Circle import Circle
from .serializers import ProfileSerializer, ExtendedProfileSerializer


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20


class TimelineHeadView(APIView):
    pagination_class = CustomPagination

    def get(self, request, user_id):
        try:
            user = get_object_or_404(UserTree, id=user_id)

            # Gather circles including groupmembers
            circles = Circle.objects.filter(
                userid=user.id,
                onlinerelation__in=['initiate', 'members', 'connections', 'groupmembers']
            )

            circles_by_user = defaultdict(lambda: defaultdict(list))
            otherperson_ids = set()

            for circle in circles:
                circles_by_user[circle.userid][circle.onlinerelation].append(circle)
                if circle.otherperson:
                    otherperson_ids.add(circle.otherperson)

            profiles = UserTree.objects.filter(id__in=otherperson_ids)
            profile_map = {p.id: p for p in profiles}

            context = {
                'request': request,
                'circles_by_user': circles_by_user,
                'profile_map': profile_map
            }

            user_profile_data = ExtendedProfileSerializer(user, context=context).data

            # Get ordered list of ancestors
            ancestors = []
            current = user.parentid
            while current:
                ancestors.append(current)
                current = current.parentid

            # Paginate ancestors
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(ancestors, request)

            serializer = ExtendedProfileSerializer(
                result_page, 
                many=True, 
                context={'request': request}
            )

            # Determine current page
            page_number = int(request.query_params.get('page', 1))

            # Construct response
            response_data = {
                "load": len(result_page),
                "results": serializer.data,
            }

            if page_number == 1:
                response_data["user_profile"] = user_profile_data

            # Add pagination metadata
            paginated_response = paginator.get_paginated_response(serializer.data)
            response_data.update({
                "count": paginated_response.data.get("count"),
                "next": paginated_response.data.get("next"),
                "previous": paginated_response.data.get("previous"),
            })

            return Response(response_data, status=status.HTTP_200_OK)

        except UserTree.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TimelineTailView(APIView):
    def get(self, request, user_id):
        try:
            profile = get_object_or_404(UserTree, id=user_id)

            # Gather circles including groupmembers
            circles = Circle.objects.filter(
                userid=profile.id,
                onlinerelation__in=['initiate', 'members', 'connections', 'groupmembers']
            )

            circles_by_user = defaultdict(lambda: defaultdict(list))
            otherperson_ids = set()

            for circle in circles:
                circles_by_user[circle.userid][circle.onlinerelation].append(circle)
                if circle.otherperson:
                    otherperson_ids.add(circle.otherperson)

            profiles = UserTree.objects.filter(id__in=otherperson_ids)
            profile_map = {p.id: p for p in profiles}

            context = {
                'request': request,
                'circles_by_user': circles_by_user,
                'profile_map': profile_map
            }

            serializer = ExtendedProfileSerializer(profile, context=context)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UserTree.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)