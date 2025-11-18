from blog.posting_blogs.blog_utils import BlogDataBuilder
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connection
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from users.models import Circle, UserTree, Petitioner
from users.login.authentication import CookieJWTAuthentication
from ..models import BaseBlogModel, Comment, UserSharedBlog, BlogLoad
from .serializers import BlogSerializer, CommentSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
        
        # Get base blogs from circle contacts and self (original posts)
        original_base_blogs = BaseBlogModel.objects.filter(userid__in=user_ids).order_by('-created_at')
        print(f"[BLOGS] Initial fetched count from DB: {original_base_blogs.count()} for user {user.id}")

        # Get shared blogs by circle users
        shared_blogs_by_circle = self.get_shared_blogs_by_circle_users(user_ids)
        
        # Combine and deduplicate blogs with proper timestamp sorting
        combined_blogs = self.combine_and_sort_blogs(original_base_blogs, shared_blogs_by_circle)
        
        print(f"[BLOGS] After combining - Original: {original_base_blogs.count()}, Shared: {len(shared_blogs_by_circle)}, Combined: {len(combined_blogs)}")

        # Prefetch UserTree objects for all authors (skip None userids)
        userids = {b['blog'].userid for b in combined_blogs if b['blog'].userid is not None}
        users = UserTree.objects.filter(id__in=userids)
        user_map = {u.id: u for u in users}

        # Prefetch Circle objects for the current user to get relations
        circles = Circle.objects.filter(userid=user.id)
        circle_map = {circle.otherperson: circle for circle in circles}

        # Get all comment IDs from all blogs using recursive SQL
        all_comment_ids = set()
        for blog_data in combined_blogs:
            blog = blog_data['blog']
            all_comment_ids.update(blog.comments)
            if blog.comments:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        WITH RECURSIVE comment_tree AS (
                            SELECT id, parent
                            FROM blog.comment
                            WHERE id = ANY(%s)
                            UNION ALL
                            SELECT c.id, c.parent
                            FROM blog.comment c
                            INNER JOIN comment_tree ct ON c.parent = ct.id AND c.parent_type = 'comment'
                        )
                        SELECT id FROM comment_tree;
                    """, [blog.comments])
                    rows = cursor.fetchall()
                    for row in rows:
                        all_comment_ids.add(row[0])
        # Prefetch all comments and their replies in a single query
        all_comments = Comment.objects.filter(id__in=all_comment_ids).order_by('created_at')

        # Build a map of comments by their parent
        comments_by_parent = {}
        for comment in all_comments:
            if comment.parent not in comments_by_parent:
                comments_by_parent[comment.parent] = []
            comments_by_parent[comment.parent].append(comment)

        # Prefetch users for all comments
        comment_user_ids = {comment.user_id for comment in all_comments}
        comment_users = UserTree.objects.filter(id__in=comment_user_ids)
        comment_user_map = {u.id: u for u in comment_users}

        # Prefetch share information for all blogs
        share_info_map = self.get_share_info_map([b['blog'] for b in combined_blogs], user.id)

        valid_content_types = {'micro', 'short_essay', 'article'}

        blog_data = []
        concrete_skip_count = 0
        author_skip_count = 0

        for blog_data_item in combined_blogs:
            base_blog = blog_data_item['blog']
            is_shared = blog_data_item['is_shared']
            share_timestamp = blog_data_item['timestamp']
            
            blog_type_raw = base_blog.type
            if not blog_type_raw:
                continue
            content_type = None
            blog_type = blog_type_raw
            for ct in valid_content_types:
                if blog_type_raw.endswith('_' + ct):
                    blog_type = blog_type_raw[:-len(ct)-1]  # Remove the suffix
                    content_type = ct
                    break
            print(f"[BLOGS] blog_type: {blog_type}, content_type: {content_type}")

            concrete_blog = self.get_concrete_blog(base_blog.id, blog_type, content_type)
            if not concrete_blog:
                concrete_skip_count += 1
                continue
            author = user_map.get(base_blog.userid)
            if not author:
                author_skip_count += 1
                continue

            # Determine relation and if it's a shared blog
            share_info = share_info_map.get(base_blog.id, {})
            
            if base_blog.userid == user.id:
                if is_shared:
                    relation = 'You shared'
                else:
                    relation = 'Your blog'
            else:
                circle = circle_map.get(base_blog.userid)
                if is_shared:
                    relation = f"{circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else 'Connection'} shared"
                else:
                    relation = circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else "Connection"

            has_liked = user.id in base_blog.likes
            has_shared = user.id in base_blog.shares
            blog_comments = self.build_comment_hierarchy_with_serializer(
                base_blog.id, comments_by_parent, comment_user_map, request
            )
            blog_data.append({
                'base': base_blog,
                'concrete': concrete_blog,
                'type': blog_type,
                'content_type': content_type,
                'author': author,
                'relation': relation,
                'has_liked': has_liked,
                'has_shared': has_shared,
                'comments': blog_comments,
                'is_shared': is_shared,
                'shared_by_user_id': share_info.get('shared_by_user_id'),
                'shared_at': share_info.get('shared_at'),
                'sort_timestamp': share_timestamp  # Keep timestamp for final sorting
            })

        print(f"[BLOGS] Number of blogs after skipping by concrete model: {len(combined_blogs) - concrete_skip_count}")
        print(f"[BLOGS] Skipped due to missing concrete model: {concrete_skip_count}")
        print(f"[BLOGS] Skipped due to missing author: {author_skip_count}")
        print(f"[BLOGS] Number of blogs sent to serializer: {len(blog_data)}")

        # Final sort by timestamp (most recent first)
        blog_data.sort(key=lambda x: x['sort_timestamp'], reverse=True)
        
        serializer = BlogSerializer(blog_data, many=True, context={'request': request})
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
                # If this blog is already in the list (as original), check if we should update the timestamp
                # For shared version of the same blog, we might want to keep the original timestamp
                # or use the share timestamp - here I'm keeping the original timestamp for consistency
                # But we mark it as shared if any user shared it
                existing_data = blog_dict[blog.id]
                existing_data['is_shared'] = True  # Mark as shared
                # You could also track multiple shares if needed
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

    def get_share_info_map(self, blogs, current_user_id):
        """Get share information for all blogs"""
        blog_ids = [blog.id for blog in blogs]
        
        # Get all shares for these blogs by circle users
        shares = UserSharedBlog.objects.filter(
            shared_blog_id__in=blog_ids
        ).order_by('-shared_at')
        
        share_info_map = {}
        for share in shares:
            if share.shared_blog_id not in share_info_map:
                share_info_map[share.shared_blog_id] = {
                    'shared_by_user_id': share.userid,
                    'shared_at': share.shared_at
                }
        
        return share_info_map

    def build_comment_hierarchy_with_serializer(self, blog_id, comments_by_parent, user_map, request):
        def build_tree(parent_id):
            comments = []
            if parent_id in comments_by_parent:
                for comment in comments_by_parent[parent_id]:
                    user = user_map.get(comment.user_id)
                    comment_serializer = CommentSerializer(
                        comment,
                        context={'request': request}
                    )
                    comment_data = comment_serializer.data
                    comment_data['replies'] = build_tree(comment.id)
                    comments.append(comment_data)
            return comments
        return build_tree(blog_id)

    def get_concrete_blog(self, blog_id, blog_type, content_type):
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
            
            # Send WebSocket update to all users who can see this blog
            self.send_blog_update(blog_id, 'like', action, len(blog.likes), user_id)
            
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
    
    def send_blog_update(self, blog_id, update_type, action, count, user_id):
        """Send WebSocket update for blog changes"""
        channel_layer = get_channel_layer()
        
        # Get all users who can see this blog (author + their circle)
        blog = BaseBlogModel.objects.get(id=blog_id)
        author_id = blog.userid
        
        # Get circle contacts for the author
        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Include author in the list
        user_ids = list(circle_user_ids) + [author_id]
        
        # Send update to each user's personal channel and the blog-specific channel
        for uid in user_ids:
            # Check if user is online
            try:
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    # Send to user's personal notification channel
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "blog_update",
                            "blog_id": str(blog_id),
                            "update_type": update_type,
                            "action": action,
                            "count": count,
                            "user_id": user_id
                        }
                    )
                else:
                    # Update BlogLoad for offline users
                    from .utils import update_blog_load_for_offline_user
                    update_blog_load_for_offline_user(uid, blog_id)
            except Petitioner.DoesNotExist:
                print(f"User with ID {uid} does not exist")
                continue
        
        # Also send to the blog-specific channel
        async_to_sync(channel_layer.group_send)(
            f"blog_{blog_id}",
            {
                "type": "blog_update",
                "blog_id": str(blog_id),
                "update_type": update_type,
                "action": action,
                "count": count,
                "user_id": user_id
            }
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
                
                # Also remove from UserSharedBlog
                UserSharedBlog.objects.filter(
                    userid=user_id, 
                    shared_blog_id=blog_id
                ).delete()
                
                # Send WebSocket update for unshare
                self.send_unshare_update(blog_id, user_id, request)
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
                
                # Send WebSocket update for share
                self.send_share_update(blog_id, user_id, request)
            
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
    
    @staticmethod
    def recursive_convert_objects_to_str(data):
        import uuid
        import datetime
        if isinstance(data, dict):
            return {k: ShareBlogView.recursive_convert_objects_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [ShareBlogView.recursive_convert_objects_to_str(i) for i in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, datetime.datetime):
            return data.isoformat()
        else:
            return data

    def send_share_update(self, blog_id, user_id, request):
        """Send complete blog data when someone shares a blog"""
        channel_layer = get_channel_layer()
        
        try:
            base_blog = BaseBlogModel.objects.get(id=blog_id)
            builder = BlogDataBuilder(request.user, request)
            blog_data = builder.get_blog_data(base_blog)
            
            if not blog_data:
                print("No blog data found for shared blog")
                return

            serializer = BlogSerializer(blog_data, context={'request': request})
            serialized_blog = serializer.data

            # Convert UUID and datetime to strings recursively before sending
            serialized_blog = self.recursive_convert_objects_to_str(serialized_blog)

            # Get the sharer's circle contacts
            sharer_circles = Circle.objects.filter(userid=user_id)
            sharer_circle_user_ids = {circle.otherperson for circle in sharer_circles if circle.otherperson}

            # Also get the original author's circle contacts (for people who follow the original author)
            original_author_id = base_blog.userid
            author_circles = Circle.objects.filter(userid=original_author_id)
            author_circle_user_ids = {circle.otherperson for circle in author_circles if circle.otherperson}

            # Combine both sets - people who follow the sharer AND people who follow the original author
            all_user_ids = sharer_circle_user_ids.union(author_circle_user_ids)
            all_user_ids = list(all_user_ids) + [user_id, original_author_id]  # Include sharer and original author

            # Remove duplicates
            all_user_ids = list(set(all_user_ids))
            
            print(f"Sending share update to user IDs: {all_user_ids}")

            for uid in all_user_ids:
                try:
                    # Check if user is online
                    user_obj = Petitioner.objects.get(id=uid)
                    if user_obj.is_online:
                        # Send WebSocket to online users
                        async_to_sync(channel_layer.group_send)(
                            f"notifications_{uid}",
                            {
                                "type": "blog_shared",
                                "blog_id": str(blog_id),
                                "action": "shared",
                                "blog": serialized_blog,
                                "shared_by_user_id": user_id,
                                "original_author_id": original_author_id,
                                "user_id": user_id
                            }
                        )
                    else:
                        # Add to new_blogs for offline users
                        blog_load, created = BlogLoad.objects.get_or_create(
                            userid=uid,
                            defaults={
                                'new_blogs': [blog_id],
                                'modified_blogs': [],
                                'loaded_blogs': []
                            }
                        )
                        if not created:
                            # Add blog to new_blogs if not already present
                            if blog_id not in blog_load.new_blogs:
                                blog_load.new_blogs.append(blog_id)
                                blog_load.save()
                except Petitioner.DoesNotExist:
                    print(f"User with ID {uid} does not exist")
                    continue

            # Always send to blog-specific channel
            async_to_sync(channel_layer.group_send)(
                f"blog_{blog_id}",
                {
                    "type": "blog_shared",
                    "blog_id": str(blog_id),
                    "action": "shared",
                    "blog": serialized_blog,
                    "shared_by_user_id": user_id,
                    "original_author_id": original_author_id,
                    "user_id": user_id
                }
            )

        except BaseBlogModel.DoesNotExist:
            print(f"Blog with ID {blog_id} not found")
            return
        except Exception as e:
            print(f"Error in send_share_update: {str(e)}")
            return

    def send_unshare_update(self, blog_id, user_id, request):
        """Send unshare update when someone removes their share"""
        channel_layer = get_channel_layer()
        
        try:
            base_blog = BaseBlogModel.objects.get(id=blog_id)
            
            # Get the sharer's circle contacts
            sharer_circles = Circle.objects.filter(userid=user_id)
            sharer_circle_user_ids = {circle.otherperson for circle in sharer_circles if circle.otherperson}

            # Also get the original author's circle contacts
            original_author_id = base_blog.userid
            author_circles = Circle.objects.filter(userid=original_author_id)
            author_circle_user_ids = {circle.otherperson for circle in author_circles if circle.otherperson}

            # Combine both sets
            all_user_ids = sharer_circle_user_ids.union(author_circle_user_ids)
            all_user_ids = list(all_user_ids) + [user_id, original_author_id]

            # Remove duplicates
            all_user_ids = list(set(all_user_ids))
            
            print(f"Sending unshare update to user IDs: {all_user_ids}")

            for uid in all_user_ids:
                try:
                    # Check if user is online
                    user_obj = Petitioner.objects.get(id=uid)
                    if user_obj.is_online:
                        # Send WebSocket to online users
                        async_to_sync(channel_layer.group_send)(
                            f"notifications_{uid}",
                            {
                                "type": "blog_unshared",
                                "blog_id": str(blog_id),
                                "action": "unshared",
                                "shared_by_user_id": user_id,
                                "original_author_id": original_author_id,
                                "user_id": user_id
                            }
                        )
                    else:
                        # Add to modified_blogs for offline users
                        blog_load, created = BlogLoad.objects.get_or_create(
                            userid=uid,
                            defaults={
                                'new_blogs': [],
                                'modified_blogs': [blog_id],
                                'loaded_blogs': []
                            }
                        )
                        if not created:
                            if blog_id not in blog_load.modified_blogs:
                                blog_load.modified_blogs.append(blog_id)
                                blog_load.save()
                except Petitioner.DoesNotExist:
                    print(f"User with ID {uid} does not exist")
                    continue

            # Always send to blog-specific channel
            async_to_sync(channel_layer.group_send)(
                f"blog_{blog_id}",
                {
                    "type": "blog_unshared",
                    "blog_id": str(blog_id),
                    "action": "unshared",
                    "shared_by_user_id": user_id,
                    "original_author_id": original_author_id,
                    "user_id": user_id
                }
            )

        except BaseBlogModel.DoesNotExist:
            print(f"Blog with ID {blog_id} not found")
            return
        except Exception as e:
            print(f"Error in send_unshare_update: {str(e)}")
            return

    def send_basic_update(self, blog_id, update_type, action, count, user_id):
        """Send basic WebSocket update for non-share actions (like unshare)"""
        channel_layer = get_channel_layer()
        
        try:
            blog = BaseBlogModel.objects.get(id=blog_id)
            author_id = blog.userid

            # Get both sharer's and author's circles
            sharer_circles = Circle.objects.filter(userid=user_id)
            sharer_circle_user_ids = {circle.otherperson for circle in sharer_circles if circle.otherperson}

            author_circles = Circle.objects.filter(userid=author_id)
            author_circle_user_ids = {circle.otherperson for circle in author_circles if circle.otherperson}

            # Combine both sets
            all_user_ids = sharer_circle_user_ids.union(author_circle_user_ids)
            all_user_ids = list(all_user_ids) + [user_id, author_id]

            # Remove duplicates
            all_user_ids = list(set(all_user_ids))

            for uid in all_user_ids:
                try:
                    user_obj = Petitioner.objects.get(id=uid)
                    if user_obj.is_online:
                        async_to_sync(channel_layer.group_send)(
                            f"notifications_{uid}",
                            {
                                "type": "blog_update",
                                "blog_id": str(blog_id),
                                "update_type": update_type,
                                "action": action,
                                "count": count,
                                "user_id": user_id
                            }
                        )
                    else:
                        # Update BlogLoad for offline users
                        blog_load, created = BlogLoad.objects.get_or_create(
                            userid=uid,
                            defaults={
                                'new_blogs': [],
                                'modified_blogs': [blog_id],
                                'loaded_blogs': []
                            }
                        )
                        if not created:
                            if blog_id not in blog_load.modified_blogs:
                                blog_load.modified_blogs.append(blog_id)
                                blog_load.save()
                except Petitioner.DoesNotExist:
                    print(f"User with ID {uid} does not exist")
                    continue

            async_to_sync(channel_layer.group_send)(
                f"blog_{blog_id}",
                {
                    "type": "blog_update",
                    "blog_id": str(blog_id),
                    "update_type": update_type,
                    "action": action,
                    "count": count,
                    "user_id": user_id
                }
            )

        except BaseBlogModel.DoesNotExist:
            print(f"Blog with ID {blog_id} not found")
            return
        except Exception as e:
            print(f"Error in send_basic_update: {str(e)}")
            return
        
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
        
        # Send WebSocket update
        self.send_comment_update(blog_id, 'comment_added', comment, user.id)
        
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def send_comment_update(self, blog_id, action, comment, user_id):
        """Send WebSocket update for comment changes"""
        channel_layer = get_channel_layer()
        
        # Get all users who can see this blog (author + their circle)
        blog = BaseBlogModel.objects.get(id=blog_id)
        author_id = blog.userid
        
        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Include author in the list
        user_ids = list(circle_user_ids) + [author_id]
        
        # Serialize comment for WebSocket
        comment_serializer = CommentSerializer(comment, context={'request': None})
        comment_data = comment_serializer.data
        
        # Send update to each user's personal channel
        for uid in user_ids:
            # Check if user is online
            try:
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "comment_update",
                            "blog_id": str(blog_id),
                            "action": action,
                            "comment": comment_data,
                            "user_id": user_id
                        }
                    )
                else:
                    # Update BlogLoad for offline users
                    from .utils import update_blog_load_for_offline_user
                    update_blog_load_for_offline_user(uid, blog_id)
            except Petitioner.DoesNotExist:
                print(f"User with ID {uid} does not exist")
                continue
        
        # Also send to the blog-specific channel
        async_to_sync(channel_layer.group_send)(
            f"blog_{blog_id}",
            {
                "type": "comment_update",
                "blog_id": str(blog_id),
                "action": action,
                "comment": comment_data,
                "user_id": user_id
            }
        )

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
        
        # Get the blog ID for this comment
        blog_id = comment.get_root_blog_id()
        if not blog_id:
            return Response(
                {'error': 'Could not find root blog for comment'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Send WebSocket update for comment like
        self.send_comment_like_update(blog_id, comment_id, action, len(comment.likes), user.id)
        
        return Response({
            'status': 'success',
            'action': action,
            'likes_count': len(comment.likes)
        })
    
    def delete(self, request, comment_id):
        # Delete a comment
        user = request.user
        comment = get_object_or_404(Comment, id=comment_id)
        blog_id = comment.parent
        
        # Check if user owns the comment
        if comment.user_id != user.id:
            return Response({'error': 'You can only delete your own comments'}, status=status.HTTP_403_FORBIDDEN)
        
        # Remove comment ID from the blog's comments list
        blog = get_object_or_404(BaseBlogModel, id=blog_id)
        if comment.id in blog.comments:
            blog.comments.remove(comment.id)
            blog.save()
        
        # Send WebSocket update for comment deletion
        self.send_comment_update(blog_id, 'comment_deleted', comment, user.id)
        
        comment.delete()
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    
    def send_comment_like_update(self, blog_id, comment_id, action, likes_count, user_id):
        """Send WebSocket update for comment like changes"""
        channel_layer = get_channel_layer()
        
        # Get all users who can see this blog (author + their circle)
        blog = BaseBlogModel.objects.get(id=blog_id)
        author_id = blog.userid
        
        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Include author in the list
        user_ids = list(circle_user_ids) + [author_id]
        
        # Send update to each user's personal channel
        for uid in user_ids:
            # Check if user is online
            try:
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "comment_like_update",
                            "blog_id": str(blog_id),
                            "comment_id": str(comment_id),
                            "action": action,
                            "likes_count": likes_count,
                            "user_id": user_id
                        }
                    )
                else:
                    # Update BlogLoad for offline users
                    from .utils import update_blog_load_for_offline_user
                    update_blog_load_for_offline_user(uid, blog_id)
            except Petitioner.DoesNotExist:
                print(f"User with ID {uid} does not exist")
                continue
        
        # Also send to the blog-specific channel
        async_to_sync(channel_layer.group_send)(
            f"blog_{blog_id}",
            {
                "type": "comment_like_update",
                "blog_id": str(blog_id),
                "comment_id": str(comment_id),
                "action": action,
                "likes_count": likes_count,
                "user_id": user_id
            }
        )
    
    def send_comment_update(self, blog_id, action, comment, user_id):
        """Send WebSocket update for comment changes"""
        # Similar implementation to CommentView's send_comment_update
        channel_layer = get_channel_layer()
        
        # Get all users who can see this blog (author + their circle)
        blog = BaseBlogModel.objects.get(id=blog_id)
        author_id = blog.userid
        
        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Include author in the list
        user_ids = list(circle_user_ids) + [author_id]
        
        # Serialize comment for WebSocket
        comment_serializer = CommentSerializer(comment, context={'request': None})
        comment_data = comment_serializer.data
        
        # Send update to each user's personal channel
        for uid in user_ids:
            # Check if user is online
            try:
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "comment_update",
                            "blog_id": str(blog_id),
                            "action": action,
                            "comment": comment_data,
                            "user_id": user_id
                        }
                    )
                else:
                    # Update BlogLoad for offline users
                    from .utils import update_blog_load_for_offline_user
                    update_blog_load_for_offline_user(uid, blog_id)
            except Petitioner.DoesNotExist:
                print(f"User with ID {uid} does not exist")
                continue
        
        # Also send to the blog-specific channel
        async_to_sync(channel_layer.group_send)(
            f"blog_{blog_id}",
            {
                "type": "comment_update",
                "blog_id": str(blog_id),
                "action": action,
                "comment": comment_data,
                "user_id": user_id
            }
        )

class CommentLikeView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        try:
            comment = Comment.objects.get(id=comment_id)
            user_id = request.user.id
            
            # Get the root blog ID for this comment
            blog_id = comment.get_root_blog_id()
            if not blog_id:
                return Response(
                    {'error': 'Could not find root blog for comment'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
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
            
            # Send WebSocket update with blog_id
            self.send_comment_like_update(blog_id, comment_id, action, len(comment.likes), user_id)
            
            return Response({
                'status': 'success',
                'action': action,
                'likes_count': len(comment.likes),
            })
            
        except Comment.DoesNotExist:
            return Response(
                {'error': 'Comment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def send_comment_like_update(self, blog_id, comment_id, action, count, user_id):
        """Send WebSocket update for comment like changes"""
        channel_layer = get_channel_layer()
        
        # Get all users who can see this blog (author + their circle)
        blog = BaseBlogModel.objects.get(id=blog_id)
        author_id = blog.userid
        
        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Include author in the list
        user_ids = list(circle_user_ids) + [author_id]
        
        # Send update to each user's personal channel
        for uid in user_ids:
            # Check if user is online
            try:
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "comment_like_update",
                            "blog_id": str(blog_id),
                            "comment_id": str(comment_id),
                            "action": action,
                            "likes_count": count,
                            "user_id": user_id
                        }
                    )
                else:
                    # Update BlogLoad for offline users
                    from .utils import update_blog_load_for_offline_user
                    update_blog_load_for_offline_user(uid, blog_id)
            except Petitioner.DoesNotExist:
                print(f"User with ID {uid} does not exist")
                continue
        
        # Also send to the blog-specific channel
        async_to_sync(channel_layer.group_send)(
            f"blog_{blog_id}",
            {
                "type": "comment_like_update",
                "blog_id": str(blog_id),
                "comment_id": str(comment_id),
                "action": action,
                "likes_count": count,
                "user_id": user_id
            }
        )

class ReplyView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def send_reply_update(self, blog_id, comment_id, reply, user_id):
        """Send WebSocket update for reply changes"""
        channel_layer = get_channel_layer()
        
        # Get all users who can see this blog (author + their circle)
        blog = BaseBlogModel.objects.get(id=blog_id)
        author_id = blog.userid
        
        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}
        
        # Include author in the list
        user_ids = list(circle_user_ids) + [author_id]
        
        # Serialize reply for WebSocket
        reply_serializer = CommentSerializer(reply, context={'request': None})
        reply_data = reply_serializer.data
        
        # Send update to each user's personal channel
        for uid in user_ids:
            # Check if user is online
            try:
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "reply_update",
                            "blog_id": str(blog_id),
                            "comment_id": str(comment_id),
                            "reply": reply_data,
                            "user_id": user_id
                        }
                    )
                else:
                    # Update BlogLoad for offline users
                    from .utils import update_blog_load_for_offline_user
                    update_blog_load_for_offline_user(uid, blog_id)
            except Petitioner.DoesNotExist:
                print(f"User with ID {uid} does not exist")
                continue
        
        # Also send to the blog-specific channel
        async_to_sync(channel_layer.group_send)(
            f"blog_{blog_id}",
            {
                "type": "reply_update",
                "blog_id": str(blog_id),
                "comment_id": str(comment_id),
                "reply": reply_data,
                "user_id": user_id
            }
        )

    def post(self, request, comment_id):
        # Create a reply to a comment
        user = request.user
        text = request.data.get('text', '').strip()
        
        if not text:
            return Response({'error': 'Reply text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        parent_comment = get_object_or_404(Comment, id=comment_id)
        
        # Get the root blog ID for the parent comment
        blog_id = parent_comment.get_root_blog_id()
        if not blog_id:
            return Response(
                {'error': 'Could not find root blog for comment'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
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
        
        # Send WebSocket update with blog_id
        self.send_reply_update(blog_id, comment_id, reply, user.id)
        
        serializer = CommentSerializer(reply, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            
            # Get comments for this blog with proper serialization
            comments = Comment.objects.filter(parent_type='blog', parent=blog_id).order_by('created_at')
            
            # Prefetch users for comments
            comment_user_ids = {comment.user_id for comment in comments}
            comment_users = UserTree.objects.filter(id__in=comment_user_ids)
            comment_user_map = {u.id: u for u in comment_users}
            
            # Build comment hierarchy using the serializer
            comments_by_parent = {}
            for comment in comments:
                if comment.parent not in comments_by_parent:
                    comments_by_parent[comment.parent] = []
                comments_by_parent[comment.parent].append(comment)
            
            blog_comments = self.build_comment_hierarchy_with_serializer(
                blog_id, comments_by_parent, comment_user_map, request
            )
            
            blog_data = {
                'base': blog,
                'concrete': concrete_blog,
                'type': blog_type,
                'content_type': content_type,
                'author': author,
                'relation': relation,
                'has_liked': has_liked,
                'has_shared': has_shared,
                'comments': blog_comments
            }
            
            # Serialize the blog data
            blog_serializer = BlogSerializer(blog_data, context={'request': request})
            
            return Response({
                'blog': blog_serializer.data,
                'comments': blog_comments
            })
            
        except BaseBlogModel.DoesNotExist:
            return Response({'error': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def build_comment_hierarchy_with_serializer(self, blog_id, comments_by_parent, user_map, request):
        """Build a hierarchical structure of comments for a blog using the serializer"""
        def build_tree(parent_id):
            comments = []
            if parent_id in comments_by_parent:
                for comment in comments_by_parent[parent_id]:
                    user = user_map.get(comment.user_id)
                    
                    # Use the serializer to ensure consistent formatting
                    comment_serializer = CommentSerializer(
                        comment, 
                        context={'request': request}
                    )
                    
                    comment_data = comment_serializer.data
                    comment_data['replies'] = build_tree(comment.id)  # Recursively build replies
                    comments.append(comment_data)
            return comments
        
        # Build tree starting from blog as parent
        return build_tree(blog_id)
    
   
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