from django.db import transaction
from django.shortcuts import get_object_or_404
from blog.models import BaseBlogModel, Comment, UserSharedBlog
from .blog_distribution import BlogDistributionService


class BlogInteractionService:
    """
    Service for handling blog interactions (likes, shares, comments)
    """
    
    def __init__(self, request):
        self.request = request
        self.distribution_service = BlogDistributionService(request)
    
    def handle_like(self, blog_id):
        """Handle blog like/unlike"""
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user_id = self.request.user.id
            
            with transaction.atomic():
                # Check if user already liked
                if user_id in blog.likes:
                    # Remove like
                    blog.likes.remove(user_id)
                    action = 'removed'
                else:
                    # Add like
                    blog.likes.append(user_id)
                    action = 'added'
                
                blog.save()
                
                # Distribute the update
                self.distribution_service.distribute_blog_interaction(
                    blog, 'like', action, len(blog.likes), user_id
                )
                
                return {
                    'status': 'success',
                    'action': action,
                    'likes_count': len(blog.likes),
                }
                
        except BaseBlogModel.DoesNotExist:
            return {'error': 'Blog not found'}
    
    def handle_share(self, blog_id):
        """Handle blog share/unshare"""
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user_id = self.request.user.id
            
            with transaction.atomic():
                # Check if user already shared this blog
                if user_id in blog.shares:
                    # Remove share
                    blog.shares.remove(user_id)
                    action = 'removed'
                    
                    # Remove from UserSharedBlog
                    UserSharedBlog.objects.filter(
                        userid=user_id, 
                        shared_blog_id=blog_id
                    ).delete()
                    
                    # Distribute unshare
                    self.distribution_service.distribute_blog_unshare(blog, user_id)
                    
                else:
                    # Add share
                    blog.shares.append(user_id)
                    action = 'added'
                    
                    # Create UserSharedBlog record
                    UserSharedBlog.objects.create(
                        userid=user_id,
                        shared_blog_id=blog_id,
                        original_author_id=blog.userid
                    )
                    
                    # Distribute share
                    self.distribution_service.distribute_blog_share(blog, user_id)
                
                blog.save()
                
                return {
                    'status': 'success',
                    'action': action,
                    'shares_count': len(blog.shares)
                }
                
        except BaseBlogModel.DoesNotExist:
            return {'error': 'Blog not found'}
    
    def handle_comment(self, blog_id, text):
        """Handle new comment creation"""
        if not text or not text.strip():
            return {'error': 'Comment text is required'}
        
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user_id = self.request.user.id
            
            with transaction.atomic():
                # Create the comment
                comment = Comment.objects.create(
                    user_id=user_id,
                    parent_type='blog',
                    parent=blog_id,
                    text=text.strip()
                )
                
                # Add comment ID to the blog's comments list
                blog.comments.append(comment.id)
                blog.save()
                
                # Prepare comment data for distribution
                from ..serializers.blog_serializers import CommentSerializer
                comment_serializer = CommentSerializer(comment, context={'request': self.request})
                comment_data = comment_serializer.data
                
                # Convert objects to strings for WebSocket
                comment_data = BlogDistributionService.recursive_convert_objects_to_str(comment_data)
                
                # Distribute comment
                self.distribution_service.distribute_comment_update(
                    blog, comment_data, 'comment_added', user_id
                )
                
                return {'comment': comment_serializer.data}
                
        except BaseBlogModel.DoesNotExist:
            return {'error': 'Blog not found'}
    
    def handle_comment_like(self, comment_id):
        """Handle comment like/unlike"""
        try:
            comment = Comment.objects.get(id=comment_id)
            user_id = self.request.user.id
            
            # Get the root blog ID for this comment
            blog_id = comment.get_root_blog_id()
            if not blog_id:
                return {'error': 'Could not find root blog for comment'}
            
            with transaction.atomic():
                # Check if user already liked
                if user_id in comment.likes:
                    # Remove like
                    comment.likes.remove(user_id)
                    action = 'removed'
                else:
                    # Add like
                    comment.likes.append(user_id)
                    action = 'added'
                
                comment.save()
                
                # Get the blog for distribution
                blog = BaseBlogModel.objects.get(id=blog_id)
                
                # Distribute comment like update
                self.distribution_service.distribute_comment_like_update(
                    blog, comment_id, action, len(comment.likes), user_id
                )
                
                return {
                    'status': 'success',
                    'action': action,
                    'likes_count': len(comment.likes),
                }
                
        except Comment.DoesNotExist:
            return {'error': 'Comment not found'}
    
    def handle_comment_delete(self, comment_id):
        """Handle comment deletion"""
        try:
            comment = Comment.objects.get(id=comment_id)
            user_id = self.request.user.id
            
            # Check if user owns the comment
            if comment.user_id != user_id:
                return {'error': 'You can only delete your own comments'}
            
            blog_id = comment.parent
            
            with transaction.atomic():
                # Remove comment ID from the blog's comments list
                blog = BaseBlogModel.objects.get(id=blog_id)
                if comment.id in blog.comments:
                    blog.comments.remove(comment.id)
                    blog.save()
                
                # Prepare comment data for distribution before deletion
                from ..serializers.blog_serializers import CommentSerializer
                comment_serializer = CommentSerializer(comment, context={'request': self.request})
                comment_data = comment_serializer.data
                comment_data = BlogDistributionService.recursive_convert_objects_to_str(comment_data)
                
                # Distribute comment deletion
                self.distribution_service.distribute_comment_update(
                    blog, comment_data, 'comment_deleted', user_id
                )
                
                # Delete the comment
                comment.delete()
                
                return {'status': 'success'}
                
        except Comment.DoesNotExist:
            return {'error': 'Comment not found'}
    
    def handle_reply(self, comment_id, text):
        """Handle reply to a comment"""
        if not text or not text.strip():
            return {'error': 'Reply text is required'}
        
        try:
            parent_comment = Comment.objects.get(id=comment_id)
            user_id = self.request.user.id
            
            # Get the root blog ID for the parent comment
            blog_id = parent_comment.get_root_blog_id()
            if not blog_id:
                return {'error': 'Could not find root blog for comment'}
            
            with transaction.atomic():
                # Create the reply
                reply = Comment.objects.create(
                    user_id=user_id,
                    parent_type='comment',
                    parent=comment_id,
                    text=text.strip()
                )
                
                # Add reply ID to the parent comment's children list
                parent_comment.children.append(reply.id)
                parent_comment.save()
                
                # Prepare reply data for distribution
                from ..serializers.blog_serializers import CommentSerializer
                reply_serializer = CommentSerializer(reply, context={'request': self.request})
                reply_data = reply_serializer.data
                reply_data = BlogDistributionService.recursive_convert_objects_to_str(reply_data)
                
                # Get the blog for distribution
                blog = BaseBlogModel.objects.get(id=blog_id)
                
                # Distribute reply using comment update (frontend can handle as reply)
                self.distribution_service.distribute_comment_update(
                    blog, reply_data, 'reply_added', user_id
                )
                
                return {'reply': reply_serializer.data}
                
        except Comment.DoesNotExist:
            return {'error': 'Parent comment not found'}