from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics

from users.login.authentication import CookieJWTAuthentication
from ..serializers.creation_serializers import BlogCreateSerializer
from ..serializers.blog_serializers import CommentSerializer
from ..services.blog_creation import BlogCreationService
from ..services.blog_distribution import BlogDistributionService
from ..services.blog_interaction import BlogInteractionService
from blog.models import BaseBlogModel, Comment
from ..utils.blog_data_builder import BlogDataBuilder
from users.models import UserTree, Circle
from django.shortcuts import get_object_or_404

class BlogCreateAPIView(APIView):
    """
    API endpoint for creating new blogs with automatic distribution
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = BlogCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Create the blog
                blog = serializer.save()
                
                # Distribute to relevant users
                distribution_service = BlogDistributionService(request)
                distribution_service.distribute_new_blog(blog)
                
                return Response({
                    'id': str(blog.id),
                    'message': 'Blog created successfully',
                    'type': request.data.get('type'),
                    'content_type': request.data.get('content_type')
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {'error': f'Blog creation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeBlogView(APIView):
    """
    Handle blog like/unlike interactions
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, blog_id):
        interaction_service = BlogInteractionService(request)
        result = interaction_service.handle_like(blog_id)
        
        if 'error' in result:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result)


class ShareBlogView(APIView):
    """
    Handle blog share/unshare interactions
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, blog_id):
        interaction_service = BlogInteractionService(request)
        result = interaction_service.handle_share(blog_id)
        
        if 'error' in result:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result)


class CommentView(APIView):
    """
    Handle blog comments
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, blog_id):
        """Get all comments for a blog"""
        comments = Comment.objects.filter(parent_type='blog', parent=blog_id).order_by('created_at')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, blog_id):
        """Create a new comment"""
        text = request.data.get('text', '').strip()
        
        interaction_service = BlogInteractionService(request)
        result = interaction_service.handle_comment(blog_id, text)
        
        if 'error' in result:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result['comment'], status=status.HTTP_201_CREATED)

class CommentDetailView(APIView):
    """
    Handle comment-specific operations (like, delete)
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        """Like or unlike a comment"""
        interaction_service = BlogInteractionService(request)
        result = interaction_service.handle_comment_like(comment_id)
        
        if 'error' in result:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result)
    
    def delete(self, request, comment_id):
        """Delete a comment"""
        interaction_service = BlogInteractionService(request)
        result = interaction_service.handle_comment_delete(comment_id)
        
        if 'error' in result:
            error_status = status.HTTP_404_NOT_FOUND if 'not found' in result['error'].lower() else status.HTTP_403_FORBIDDEN
            return Response(
                {'error': result['error']}, 
                status=error_status
            )
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)

class ReplyView(APIView):
    """
    Handle replies to comments
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        """Create a reply to a comment"""
        text = request.data.get('text', '').strip()
        
        interaction_service = BlogInteractionService(request)
        result = interaction_service.handle_reply(comment_id, text)
        
        if 'error' in result:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result['reply'], status=status.HTTP_201_CREATED)


class CircleBlogsView(generics.GenericAPIView):
    """
    Get blogs for user's circle (including shared blogs)
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Your existing implementation for fetching circle blogs
        # This can be refactored later if needed, but works fine as is
        #
        #
        from ...blogpage.views import CircleBlogsView as OriginalCircleBlogsView
        original_view = OriginalCircleBlogsView()
        original_view.request = request
        return original_view.get(request)


class BlogDetailView(APIView):
    """
    Get detailed blog data
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, blog_id):
        # Your existing implementation for blog details
            
        from ...blogpage.views import BlogDetailView as OriginalBlogDetailView
        original_view = OriginalBlogDetailView()
        original_view.request = request
        return original_view.get(request, blog_id)