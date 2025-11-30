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
from blog.models import BaseBlogModel, Comment, UserSharedBlog
from ..utils.blog_data_builder import BlogDataBuilder
from users.models import UserTree, Circle
from django.shortcuts import get_object_or_404
from django.db import connection
from ..serializers.blog_serializers import BlogSerializer

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
    Get blogs for user's circle (including shared blogs) - New Implementation
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get all circle contacts for current user
        circles_qs = Circle.objects.filter(userid=user.id)
        circle_user_ids = {circle.otherperson for circle in circles_qs if circle.otherperson}
        # Include self in the list of users to get blogs from
        user_ids = list(circle_user_ids) + [user.id]
        
        # Get base blogs from circle contacts and self (original posts)
        original_base_blogs = BaseBlogModel.objects.filter(userid__in=user_ids).order_by('-created_at')
        print(f"[BLOGS] Initial fetched count from DB: {original_base_blogs.count()} for user {user.id}")

        # Get shared blogs by circle users
        shared_blogs_by_circle = self.get_shared_blogs_by_circle_users(user_ids)
        
        # Combine and deduplicate blogs with proper timestamp sorting
        combined_blogs = self.combine_and_sort_blogs(original_base_blogs, shared_blogs_by_circle)
        
        print(f"[BLOGS] After combining - Original: {original_base_blogs.count()}, Shared: {len(shared_blogs_by_circle)}, Combined: {len(combined_blogs)}")

        # Build blog data using the BlogDataBuilder
        blog_data_builder = BlogDataBuilder(user, request)
        processed_blogs = []
        
        for blog_data_item in combined_blogs:
            base_blog = blog_data_item['blog']
            is_shared = blog_data_item['is_shared']
            share_timestamp = blog_data_item['timestamp']
            
            # Use BlogDataBuilder to get complete blog data
            blog_data = blog_data_builder.get_blog_data(base_blog)
            if not blog_data:
                continue
                
            # Add share information
            blog_data['is_shared'] = is_shared
            blog_data['sort_timestamp'] = share_timestamp
            
            # Get share info if it's a shared blog
            if is_shared:
                share_info = self.get_share_info(base_blog.id, user.id)
                blog_data['shared_by_user_id'] = share_info.get('shared_by_user_id')
                blog_data['shared_at'] = share_info.get('shared_at')
            
            processed_blogs.append(blog_data)

        # Final sort by timestamp (most recent first)
        processed_blogs.sort(key=lambda x: x['sort_timestamp'], reverse=True)
        
        # Serialize using the new BlogSerializer
        serializer = BlogSerializer(processed_blogs, many=True, context={'request': request})
        return Response(serializer.data)

    def get_shared_blogs_by_circle_users(self, user_ids):
        """Get blogs shared by circle users with share timestamp"""
        # Get recent shares by circle users
        recent_shared_blogs = UserSharedBlog.objects.filter(
            userid__in=user_ids
        ).order_by('-shared_at')
        
        # Get the actual blog objects that were shared
        shared_blog_ids = [share.shared_blog_id for share in recent_shared_blogs]
        shared_blogs = BaseBlogModel.objects.filter(id__in=shared_blog_ids)
        
        # Create a mapping for quick access
        shared_blog_map = {blog.id: blog for blog in shared_blogs}
        
        # Return blogs with their share timestamps
        result = []
        for share in recent_shared_blogs:
            blog = shared_blog_map.get(share.shared_blog_id)
            if blog:
                result.append({
                    'blog': blog,
                    'share_timestamp': share.shared_at,
                    'is_shared': True
                })
                
        return result

    def combine_and_sort_blogs(self, original_blogs, shared_blogs):
        """Combine original and shared blogs, deduplicate and sort by timestamp"""
        blog_dict = {}  # Use dict to deduplicate by blog ID
        
        # Process original blogs (use created_at as timestamp)
        for blog in original_blogs:
            if blog.id not in blog_dict:
                blog_dict[blog.id] = {
                    'blog': blog,
                    'timestamp': blog.created_at,
                    'is_shared': False
                }
        
        # Process shared blogs (use share_timestamp, prefer later timestamp if already exists)
        for shared_data in shared_blogs:
            blog = shared_data['blog']
            share_timestamp = shared_data['share_timestamp']
            
            if blog.id in blog_dict:
                # If this blog is already in the list (as original), mark it as shared
                existing_data = blog_dict[blog.id]
                existing_data['is_shared'] = True
            else:
                # New blog (only shared, not original)
                blog_dict[blog.id] = {
                    'blog': blog,
                    'timestamp': share_timestamp,
                    'is_shared': True
                }
        
        # Convert to list and sort by timestamp (most recent first)
        combined_list = list(blog_dict.values())
        combined_list.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return combined_list

    def get_share_info(self, blog_id, current_user_id):
        """Get share information for a specific blog"""
        try:
            share = UserSharedBlog.objects.filter(
                shared_blog_id=blog_id
            ).order_by('-shared_at').first()
            
            if share:
                return {
                    'shared_by_user_id': share.userid,
                    'shared_at': share.shared_at
                }
        except UserSharedBlog.DoesNotExist:
            pass
        
        return {}


class BlogDetailView(APIView):
    """
    Get detailed blog data - New Implementation
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, blog_id):
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user = request.user
            
            # Use BlogDataBuilder to get complete blog data
            blog_data_builder = BlogDataBuilder(user, request)
            blog_data = blog_data_builder.get_blog_data(blog)
            
            if not blog_data:
                return Response({'error': 'Blog data not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Serialize the blog data
            blog_serializer = BlogSerializer(blog_data, context={'request': request})
            
            return Response({
                'blog': blog_serializer.data,
                'comments': blog_data.get('comments', [])
            })
            
        except BaseBlogModel.DoesNotExist:
            return Response({'error': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)