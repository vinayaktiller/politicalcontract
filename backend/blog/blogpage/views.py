# views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.shortcuts import get_object_or_404

from users.models import Circle, UserTree
from users.login.authentication import CookieJWTAuthentication
from ..models import BaseBlogModel, Comment
from .serializers import BlogSerializer, CommentSerializer


class CircleBlogsView(generics.GenericAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Get all circle contacts for current user
        circles_qs = Circle.objects.filter(userid=user.id)
        circle_user_ids = {circle.otherperson for circle in circles_qs if circle.otherperson}

        # Include self in the list of users to get blogs from
        user_ids = list(circle_user_ids) + [user.id]

        # Get base blogs from circle contacts and self
        base_blogs = BaseBlogModel.objects.filter(userid__in=user_ids).order_by('-created_at')

        # Prefetch UserTree objects for all authors (skip None userids)
        userids = {b.userid for b in base_blogs if b.userid is not None}
        users = UserTree.objects.filter(id__in=userids)
        user_map = {u.id: u for u in users}

        # Prefetch Circle objects for the current user to get relations
        circles = Circle.objects.filter(userid=user.id)
        circle_map = {circle.otherperson: circle for circle in circles}

        # Build blog data list
        blog_data = []
        for base_blog in base_blogs:
            blog_type_raw = base_blog.type
            if not blog_type_raw:
                continue

            # Split using rsplit so we split at the RIGHTMOST underscore.
            # Example: "report_insight_micro" -> ("report_insight", "micro")
            if '_' in blog_type_raw:
                blog_type, content_type = blog_type_raw.rsplit('_', 1)
            else:
                blog_type = blog_type_raw
                content_type = None

            # Get the concrete blog instance
            concrete_blog = self.get_concrete_blog(base_blog.id, blog_type, content_type)
            if not concrete_blog:
                continue

            # Get author and relation
            author = user_map.get(base_blog.userid)
            if not author:
                # If author not found in prefetch, skip (or optionally load on demand)
                continue

            if base_blog.userid == user.id:
                relation = 'Your blog'
            else:
                circle = circle_map.get(base_blog.userid)
                relation = circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else "Connection"

            # Check if current user has liked this blog
            has_liked = user.id in base_blog.likes
            has_shared = user.id in base_blog.shares

            blog_data.append({
                'base': base_blog,
                'concrete': concrete_blog,
                'type': blog_type,           # e.g. 'report_insight'
                'content_type': content_type, # e.g. 'micro'
                'author': author,
                'relation': relation,
                'has_liked': has_liked,
                'has_shared': has_shared
            })

        # Serialize the data
        serializer = BlogSerializer(blog_data, many=True, context={'request': request})
        return Response(serializer.data)

    def get_concrete_blog(self, blog_id, blog_type, content_type):
        # Import models locally to avoid circular imports
        if blog_type == 'journey':
            from ..models import (
                MicroJourneyBlog, ShortEssayJourneyBlog, ArticleJourneyBlog
            )
            model_map = {
                'micro': MicroJourneyBlog,
                'short_essay': ShortEssayJourneyBlog,
                'article': ArticleJourneyBlog
            }

        elif blog_type == 'milestone':
            from ..models import (
                MicroMilestoneJourneyBlog, ShortEssayMilestoneJourneyBlog,
                ArticleMilestoneJourneyBlog
            )
            model_map = {
                'micro': MicroMilestoneJourneyBlog,
                'short_essay': ShortEssayMilestoneJourneyBlog,
                'article': ArticleMilestoneJourneyBlog
            }

        elif blog_type == 'report_insight':
            from ..models import (
                report_insight_micro, report_insight_short_essay, report_insight_article
            )
            model_map = {
                'micro': report_insight_micro,
                'short_essay': report_insight_short_essay,
                'article': report_insight_article
            }

        elif blog_type == 'successful_experience':
            from ..models import (
                MicroSuccessfulExperience, ShortEssaySuccessfulExperience,
                ArticleSuccessfulExperience
            )
            model_map = {
                'micro': MicroSuccessfulExperience,
                'short_essay': ShortEssaySuccessfulExperience,
                'article': ArticleSuccessfulExperience
            }

        elif blog_type == 'answering_question':
            from ..models import (
                MicroAnsweringQuestionBlog, ShortEssayAnsweringQuestionBlog,
                ArticleAnsweringQuestionBlog
            )
            model_map = {
                'micro': MicroAnsweringQuestionBlog,
                'short_essay': ShortEssayAnsweringQuestionBlog,
                'article': ArticleAnsweringQuestionBlog
            }

        elif blog_type == 'consumption':
            from ..models import (
                MicroConsumption, ShortEssayConsumption, ArticleConsumption
            )
            model_map = {
                'micro': MicroConsumption,
                'short_essay': ShortEssayConsumption,
                'article': ArticleConsumption
            }

        elif blog_type == 'failed_initiation':
            from ..models import (
                MicroFailedInitiationExperience, ShortEssayFailedInitiationExperience,
                ArticleFailedInitiationExperience
            )
            model_map = {
                'micro': MicroFailedInitiationExperience,
                'short_essay': ShortEssayFailedInitiationExperience,
                'article': ArticleFailedInitiationExperience
            }
        else:
            return None

        if not content_type or content_type not in model_map:
            return None

        try:
            return model_map[content_type].objects.get(id=blog_id)
        except model_map[content_type].DoesNotExist:
            return None


class BlogDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, blog_id):
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user = request.user
            
            # Get blog type and content type
            blog_type_raw = blog.type
            if not blog_type_raw:
                return Response({'error': 'Blog type not found'}, status=status.HTTP_404_NOT_FOUND)
                
            if '_' in blog_type_raw:
                blog_type, content_type = blog_type_raw.rsplit('_', 1)
            else:
                blog_type = blog_type_raw
                content_type = None
                
            # Get the concrete blog instance
            concrete_blog = self.get_concrete_blog(blog.id, blog_type, content_type)
            if not concrete_blog:
                return Response({'error': 'Concrete blog not found'}, status=status.HTTP_404_NOT_FOUND)
                
            # Get author and relation
            author = UserTree.objects.filter(id=blog.userid).first()
            if not author:
                return Response({'error': 'Author not found'}, status=status.HTTP_404_NOT_FOUND)
                
            if blog.userid == user.id:
                relation = 'Your Journey'
            else:
                circle = Circle.objects.filter(userid=user.id, otherperson=blog.userid).first()
                relation = circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else "Connection"
                
            # Check if current user has liked this blog
            has_liked = user.id in blog.likes
            has_shared = user.id in blog.shares
            
            # Get comments for this blog
            comments = Comment.objects.filter(parent_type='blog', parent=blog_id).order_by('created_at')
            comment_serializer = CommentSerializer(comments, many=True, context={'request': request})
            
            blog_data = {
                'base': blog,
                'concrete': concrete_blog,
                'type': blog_type,
                'content_type': content_type,
                'author': author,
                'relation': relation,
                'has_liked': has_liked,
                'has_shared': has_shared
            }
            
            # Serialize the blog data
            blog_serializer = BlogSerializer(blog_data, context={'request': request})
            
            return Response({
                'blog': blog_serializer.data,
                'comments': comment_serializer.data
            })
            
        except BaseBlogModel.DoesNotExist:
            return Response({'error': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def get_concrete_blog(self, blog_id, blog_type, content_type):
        # Same implementation as in CircleBlogsView
        if blog_type == 'journey':
            from ..models import (
                MicroJourneyBlog, ShortEssayJourneyBlog, ArticleJourneyBlog
            )
            model_map = {
                'micro': MicroJourneyBlog,
                'short_essay': ShortEssayJourneyBlog,
                'article': ArticleJourneyBlog
            }

        elif blog_type == 'milestone':
            from ..models import (
                MicroMilestoneJourneyBlog, ShortEssayMilestoneJourneyBlog,
                ArticleMilestoneJourneyBlog
            )
            model_map = {
                'micro': MicroMilestoneJourneyBlog,
                'short_essay': ShortEssayMilestoneJourneyBlog,
                'article': ArticleMilestoneJourneyBlog
            }

        elif blog_type == 'report_insight':
            from ..models import (
                report_insight_micro, report_insight_short_essay, report_insight_article
            )
            model_map = {
                'micro': report_insight_micro,
                'short_essay': report_insight_short_essay,
                'article': report_insight_article
            }

        elif blog_type == 'successful_experience':
            from ..models import (
                MicroSuccessfulExperience, ShortEssaySuccessfulExperience,
                ArticleSuccessfulExperience
            )
            model_map = {
                'micro': MicroSuccessfulExperience,
                'short_essay': ShortEssaySuccessfulExperience,
                'article': ArticleSuccessfulExperience
            }

        elif blog_type == 'answering_question':
            from ..models import (
                MicroAnsweringQuestionBlog, ShortEssayAnsweringQuestionBlog,
                ArticleAnsweringQuestionBlog
            )
            model_map = {
                'micro': MicroAnsweringQuestionBlog,
                'short_essay': ShortEssayAnsweringQuestionBlog,
                'article': ArticleAnsweringQuestionBlog
            }

        elif blog_type == 'consumption':
            from ..models import (
                MicroConsumption, ShortEssayConsumption, ArticleConsumption
            )
            model_map = {
                'micro': MicroConsumption,
                'short_essay': ShortEssayConsumption,
                'article': ArticleConsumption
            }

        elif blog_type == 'failed_initiation':
            from ..models import (
                MicroFailedInitiationExperience, ShortEssayFailedInitiationExperience,
                ArticleFailedInitiationExperience
            )
            model_map = {
                'micro': MicroFailedInitiationExperience,
                'short_essay': ShortEssayFailedInitiationExperience,
                'article': ArticleFailedInitiationExperience
            }
        else:
            return None

        if not content_type or content_type not in model_map:
            return None

        try:
            return model_map[content_type].objects.get(id=blog_id)
        except model_map[content_type].DoesNotExist:
            return None


class LikeBlogView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, blog_id):
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user_id = request.user.id
            
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
            
            return Response({
                'status': 'success',
                'action': action,
                'likes_count': len(blog.likes),
            })
            
        except BaseBlogModel.DoesNotExist:
            return Response(
                {'error': 'Blog not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ShareBlogView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, blog_id):
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            user_id = request.user.id
            
            # Check if user already shared this blog
            if user_id in blog.shares:
                # Remove share
                blog.shares.remove(user_id)
                action = 'removed'
            else:
                # Add share
                blog.shares.append(user_id)
                action = 'added'
            
            blog.save()
            
            return Response({
                'status': 'success',
                'action': action,
                'shares_count': len(blog.shares)
            })
            
        except BaseBlogModel.DoesNotExist:
            return Response(
                {'error': 'Blog not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CommentView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, blog_id):
        # Get all comments for a blog
        comments = Comment.objects.filter(parent_type='blog', parent=blog_id).order_by('created_at')
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, blog_id):
        # Create a new comment
        user = request.user
        text = request.data.get('text', '').strip()
        
        if not text:
            return Response({'error': 'Comment text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the comment
        comment = Comment.objects.create(
            user_id=user.id,
            parent_type='blog',
            parent=blog_id,
            text=text
        )
        
        # Add comment ID to the blog's comments list
        blog = get_object_or_404(BaseBlogModel, id=blog_id)
        blog.comments.append(comment.id)
        blog.save()
        
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        # Like or unlike a comment
        user = request.user
        comment = get_object_or_404(Comment, id=comment_id)
        
        if user.id in comment.likes:
            # Unlike
            comment.likes.remove(user.id)
            action = 'removed'
        else:
            # Like
            comment.likes.append(user.id)
            action = 'added'
            
        comment.save()
        
        return Response({
            'status': 'success',
            'action': action,
            'likes_count': len(comment.likes)
        })
    
    def delete(self, request, comment_id):
        # Delete a comment
        user = request.user
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if user owns the comment
        if comment.user_id != user.id:
            return Response({'error': 'You can only delete your own comments'}, status=status.HTTP_403_FORBIDDEN)
        
        # Remove comment ID from the blog's comments list
        blog = get_object_or_404(BaseBlogModel, id=comment.parent)
        if comment.id in blog.comments:
            blog.comments.remove(comment.id)
            blog.save()
        
        comment.delete()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)


class ReplyView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        # Create a reply to a comment
        user = request.user
        text = request.data.get('text', '').strip()
        
        if not text:
            return Response({'error': 'Reply text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        parent_comment = get_object_or_404(Comment, id=comment_id)
        
        # Create the reply
        reply = Comment.objects.create(
            user_id=user.id,
            parent_type='comment',
            parent=comment_id,
            text=text
        )
        
        # Add reply ID to the parent comment's children list
        parent_comment.children.append(reply.id)
        parent_comment.save()
        
        serializer = CommentSerializer(reply, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)