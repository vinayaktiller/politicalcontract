# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .serializers import JourneyBlogSerializer
from ..models import (
    MicroJourneyBlog, 
    ShortEssayJourneyBlog, 
    ArticleJourneyBlog
)

class JourneyBlogAPIView(APIView):
    def get_object(self, pk):
        """Retrieve object from any journey blog type by UUID"""
        for model in [MicroJourneyBlog, ShortEssayJourneyBlog, ArticleJourneyBlog]:
            try:
                return model.objects.get(pk=pk)
            except model.DoesNotExist:
                continue
        return None

    def get(self, request, pk=None):
        context = {'request': request, 'userid': request.user.id}
        
        if pk:
            obj = self.get_object(pk)
            if not obj:
                return Response(status=status.HTTP_404_NOT_FOUND)
            serializer = JourneyBlogSerializer(obj, context=context)
            return Response(serializer.data)
        
        # Combine all blog types
        micro = MicroJourneyBlog.objects.all()
        short_essay = ShortEssayJourneyBlog.objects.all()
        article = ArticleJourneyBlog.objects.all()
        
        all_blogs = list(micro) + list(short_essay) + list(article)
        serializer = JourneyBlogSerializer(all_blogs, many=True, context=context)
        return Response(serializer.data)

    def post(self, request):
        serializer = JourneyBlogSerializer(
            data=request.data, 
            context={
                'request': request, 
                'userid': request.user.id
            }
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        serializer = JourneyBlogSerializer(
            obj, 
            data=request.data, 
            partial=True,
            context={
                'request': request, 
                'userid': request.user.id
            }
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)