from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import Circle, Petitioner
from blog.models import BlogLoad, BaseBlogModel
from ..utils.blog_data_builder import BlogDataBuilder
from ..serializers.blog_serializers import BlogSerializer

class BlogDistributionService:
    """
    Service for distributing blog updates, likes, shares, and comments
    to relevant users via WebSocket and offline storage.
    """
    
    def __init__(self, request):
        self.request = request
        self.channel_layer = get_channel_layer()
    
    def get_audience_for_blog(self, blog):
        """
        Get all users who should receive updates for a blog:
        - Author's circle contacts
        - Author themselves
        - People who shared the blog (so they get like/share count updates)
        """
        author_id = blog.userid
        
        # Get author's circle contacts
        author_circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in author_circles if circle.otherperson}
        
        # Include people who shared this blog (they should get updates too)
        sharer_ids = set(blog.shares) if blog.shares else set()
        
        # Include author in the audience
        audience = list(circle_user_ids.union({author_id}).union(sharer_ids))
        
        print(f"[BLOG DISTRIBUTION] Audience for blog {blog.id}: {audience}")
        return audience
    
    def get_audience_for_shared_blog(self, blog, sharer_id):
        """
        Get audience for shared blog:
        - Author's circle contacts
        - Sharer's circle contacts  
        - Both author and sharer
        - People who already shared the blog
        """
        author_id = blog.userid
        
        # Get author's circle
        author_circles = Circle.objects.filter(userid=author_id)
        author_circle_ids = {circle.otherperson for circle in author_circles if circle.otherperson}
        
        # Get sharer's circle
        sharer_circles = Circle.objects.filter(userid=sharer_id)
        sharer_circle_ids = {circle.otherperson for circle in sharer_circles if circle.otherperson}
        
        # Get people who already shared this blog
        existing_sharers = set(blog.shares) if blog.shares else set()
        
        # Combine all audiences: both circles + author + sharer + existing sharers
        audience = author_circle_ids.union(sharer_circle_ids).union({author_id, sharer_id}).union(existing_sharers)
        audience = list(audience)
        
        print(f"[BLOG DISTRIBUTION] Audience for shared blog {blog.id}: {audience}")
        return audience
    
    def get_audience_for_unshare(self, blog, unsharer_id):
        """
        Get audience for unshare event - includes everyone who might have seen the share
        and needs to know it's been removed
        """
        author_id = blog.userid
        
        # Get author's circle
        author_circles = Circle.objects.filter(userid=author_id)
        author_circle_ids = {circle.otherperson for circle in author_circles if circle.otherperson}
        
        # Get unsharer's circle (people who saw the share)
        unsharer_circles = Circle.objects.filter(userid=unsharer_id)
        unsharer_circle_ids = {circle.otherperson for circle in unsharer_circles if circle.otherperson}
        
        # Get people who still share this blog (they need share count updates)
        remaining_sharers = set(blog.shares) if blog.shares else set()
        
        # Combine: both circles + author + unsharer + remaining sharers
        audience = author_circle_ids.union(unsharer_circle_ids).union({author_id, unsharer_id}).union(remaining_sharers)
        audience = list(audience)
        
        print(f"[BLOG DISTRIBUTION] Audience for unshare blog {blog.id}: {audience}")
        return audience
    
    def prepare_blog_data(self, blog):
        """
        Prepare complete blog data for WebSocket transmission
        """
        try:
            builder = BlogDataBuilder(self.request.user, self.request)
            blog_data = builder.get_blog_data(blog)
            
            if not blog_data:
                print(f"[BLOG DISTRIBUTION] No blog data found for blog {blog.id}")
                return None
            
            # Serialize the blog data
            serializer = BlogSerializer(blog_data, context={'request': self.request})
            serialized_data = serializer.data
            
            # Convert UUIDs and datetime objects to strings for JSON serialization
            serialized_data = self.recursive_convert_objects_to_str(serialized_data)
            
            return serialized_data
            
        except Exception as e:
            print(f"[BLOG DISTRIBUTION] Error preparing blog data: {str(e)}")
            return None
    
    def send_to_online_users(self, user_ids, message_data):
        """
        Send WebSocket message to online users
        """
        sent_count = 0
        for user_id in user_ids:
            try:
                user_obj = Petitioner.objects.get(id=user_id)
                if user_obj.is_online:
                    async_to_sync(self.channel_layer.group_send)(
                        f"notifications_{user_id}",
                        message_data
                    )
                    print(f"[BLOG DISTRIBUTION] Sent to online user {user_id}")
                    sent_count += 1
                else:
                    print(f"[BLOG DISTRIBUTION] User {user_id} is offline, storing in BlogLoad")
                    
            except Petitioner.DoesNotExist:
                print(f"[BLOG DISTRIBUTION] User {user_id} does not exist")
                continue
        
        print(f"[BLOG DISTRIBUTION] Successfully sent to {sent_count} online users")
        return sent_count
    
    def update_blog_load_for_offline_users(self, user_ids, blog_id, list_type='new_blogs'):
        """
        Update BlogLoad for offline users
        """
        updated_count = 0
        for user_id in user_ids:
            try:
                user_obj = Petitioner.objects.get(id=user_id)
                if not user_obj.is_online:
                    self._update_single_blog_load(user_id, blog_id, list_type)
                    print(f"[BLOG DISTRIBUTION] Updated BlogLoad for offline user {user_id}")
                    updated_count += 1
                    
            except Petitioner.DoesNotExist:
                print(f"[BLOG DISTRIBUTION] User {user_id} does not exist")
                continue
        
        print(f"[BLOG DISTRIBUTION] Successfully updated BlogLoad for {updated_count} offline users")
        return updated_count
    
    def _update_single_blog_load(self, user_id, blog_id, list_type):
        """
        Update BlogLoad for a single user
        """
        try:
            blog_load, created = BlogLoad.objects.get_or_create(
                userid=user_id,
                defaults={
                    'new_blogs': [],
                    'modified_blogs': [],
                    'loaded_blogs': [],
                    'deleted_blogs': [],
                    list_type: [blog_id]
                }
            )
            
            if not created:
                current_list = getattr(blog_load, list_type)
                if blog_id not in current_list:
                    current_list.append(blog_id)
                    setattr(blog_load, list_type, current_list)
                    # blog_load.outdated = True
                    
                    blog_load.save()
                    
        except Exception as e:
            print(f"[BLOG DISTRIBUTION] Error updating BlogLoad for user {user_id}: {str(e)}")
    
    def distribute_new_blog(self, blog):
        """
        Distribute a newly created blog to relevant users
        """
        print(f"[BLOG DISTRIBUTION] Distributing new blog: {blog.id}")
        
        audience = self.get_audience_for_blog(blog)
        blog_data = self.prepare_blog_data(blog)
        
        if not blog_data:
            print(f"[BLOG DISTRIBUTION] Failed to prepare blog data for {blog.id}")
            return
        
        # Determine blog base type for notification
        blog_type_parts = blog.type.split('_')
        blog_base_type = blog_type_parts[0] if blog_type_parts else blog.type
        
        message_data = {
            "type": "blog_created",
            "blog_id": str(blog.id),
            "action": "blog_created", 
            "blog_type": blog_base_type,
            "blog": blog_data,
            "user_id": self.request.user.id
        }
        
        # Send to online users
        online_sent = self.send_to_online_users(audience, message_data)
        
        # Update BlogLoad for offline users
        offline_updated = self.update_blog_load_for_offline_users(audience, blog.id, 'new_blogs')
        
        # Also send to blog-specific channel for real-time subscribers
        async_to_sync(self.channel_layer.group_send)(
            f"blog_{blog.id}",
            message_data
        )
        
        print(f"[BLOG DISTRIBUTION] Successfully distributed blog {blog.id} to {len(audience)} users "
              f"({online_sent} online, {offline_updated} offline)")
    
    def distribute_blog_share(self, blog, sharer_id):
        """
        Distribute a blog share event
        """
        print(f"[BLOG DISTRIBUTION] Distributing blog share: {blog.id} by user {sharer_id}")
        
        audience = self.get_audience_for_shared_blog(blog, sharer_id)
        blog_data = self.prepare_blog_data(blog)
        
        if not blog_data:
            print(f"[BLOG DISTRIBUTION] Failed to prepare blog data for share {blog.id}")
            return
        
        message_data = {
            "type": "blog_shared", 
            "blog_id": str(blog.id),
            "action": "shared",
            "blog": blog_data,
            "shared_by_user_id": sharer_id,
            "original_author_id": blog.userid,
            "user_id": self.request.user.id,
            "shares_count": len(blog.shares) if blog.shares else 0
        }
        
        # Send to online users
        online_sent = self.send_to_online_users(audience, message_data)
        
        # Update BlogLoad for offline users
        offline_updated = self.update_blog_load_for_offline_users(audience, blog.id, 'new_blogs')
        
        # Send to blog-specific channel
        async_to_sync(self.channel_layer.group_send)(
            f"blog_{blog.id}",
            message_data
        )
        
        print(f"[BLOG DISTRIBUTION] Successfully distributed share for blog {blog.id} to {len(audience)} users "
              f"({online_sent} online, {offline_updated} offline)")
    
    def distribute_blog_unshare(self, blog, unsharer_id):
        """
        Distribute a blog unshare event
        """
        print(f"[BLOG DISTRIBUTION] Distributing blog unshare: {blog.id} by user {unsharer_id}")
        
        # Get audience for unshare - includes everyone who might have seen the share
        audience = self.get_audience_for_unshare(blog, unsharer_id)
        
        message_data = {
            "type": "blog_unshared",
            "blog_id": str(blog.id), 
            "action": "unshared",
            "shared_by_user_id": unsharer_id,
            "original_author_id": blog.userid,
            "user_id": self.request.user.id,
            "shares_count": len(blog.shares) if blog.shares else 0
        }
        
        # Send to online users
        online_sent = self.send_to_online_users(audience, message_data)
        
        # For offline users: if they have no other connection to the blog, mark as deleted
        # Otherwise mark as modified
        for user_id in audience:
            try:
                user_obj = Petitioner.objects.get(id=user_id)
                if not user_obj.is_online:
                    # Check if user has any other connection to this blog
                    should_delete = self._should_delete_blog_for_user(user_id, blog, unsharer_id)
                    if should_delete:
                        self._update_single_blog_load(user_id, blog.id, 'deleted_blogs')
                        print(f"[BLOG DISTRIBUTION] Marked blog {blog.id} as deleted for offline user {user_id}")
                    else:
                        self._update_single_blog_load(user_id, blog.id, 'modified_blogs')
                        print(f"[BLOG DISTRIBUTION] Marked blog {blog.id} as modified for offline user {user_id}")
                    
            except Petitioner.DoesNotExist:
                continue
        
        # Send to blog-specific channel
        async_to_sync(self.channel_layer.group_send)(
            f"blog_{blog.id}",
            message_data
        )
        
        print(f"[BLOG DISTRIBUTION] Successfully distributed unshare for blog {blog.id} to {len(audience)} users "
              f"({online_sent} online)")
    
    def _should_delete_blog_for_user(self, user_id, blog, unsharer_id):
        """
        Check if a blog should be deleted (not just modified) for a user when unshared.
        Returns True if user has no other connection to the blog (not in author's circle, 
        not the author, not sharing it themselves, not connected to other sharers)
        """
        author_id = blog.userid
        
        # If user is the author, they should keep the blog
        if user_id == author_id:
            return False
            
        # If user is sharing the blog themselves, they should keep it
        if blog.shares and user_id in blog.shares:
            return False
            
        # Check if user is in author's circle
        author_circles = Circle.objects.filter(userid=author_id, otherperson=user_id)
        if author_circles.exists():
            return False
            
        # Check if user is connected to any other sharers
        other_sharers = set(blog.shares) if blog.shares else set()
        other_sharers.discard(unsharer_id)  # Remove the unsharer
        
        for sharer_id in other_sharers:
            sharer_circles = Circle.objects.filter(userid=sharer_id, otherperson=user_id)
            if sharer_circles.exists():
                return False
                
        # If none of the above conditions are met, user should no longer see this blog
        return True
    
    def distribute_blog_interaction(self, blog, interaction_type, action, count, user_id):
        """
        Distribute blog interactions (likes, etc.)
        """
        print(f"[BLOG DISTRIBUTION] Distributing {interaction_type} {action} for blog {blog.id}")
        
        audience = self.get_audience_for_blog(blog)
        
        message_data = {
            "type": "blog_update",
            "blog_id": str(blog.id),
            "update_type": interaction_type,
            "action": action,
            "count": count,
            "user_id": user_id
        }
        
        # Send to online users
        online_sent = self.send_to_online_users(audience, message_data)
        
        # Update BlogLoad for offline users (mark as modified)
        offline_updated = self.update_blog_load_for_offline_users(audience, blog.id, 'modified_blogs')
        
        # Send to blog-specific channel
        async_to_sync(self.channel_layer.group_send)(
            f"blog_{blog.id}",
            message_data
        )
        
        print(f"[BLOG DISTRIBUTION] Successfully distributed {interaction_type} {action} for blog {blog.id} "
              f"to {len(audience)} users ({online_sent} online, {offline_updated} offline)")
    
    def distribute_comment_update(self, blog, comment_data, action, user_id):
        """
        Distribute comment updates (new comment, deleted comment)
        """
        print(f"[BLOG DISTRIBUTION] Distributing comment {action} for blog {blog.id}")
        
        audience = self.get_audience_for_blog(blog)
        
        message_data = {
            "type": "comment_update",
            "blog_id": str(blog.id),
            "action": action,
            "comment": comment_data,
            "user_id": user_id
        }
        
        # Send to online users
        online_sent = self.send_to_online_users(audience, message_data)
        
        # Update BlogLoad for offline users
        offline_updated = self.update_blog_load_for_offline_users(audience, blog.id, 'modified_blogs')
        
        # Send to blog-specific channel
        async_to_sync(self.channel_layer.group_send)(
            f"blog_{blog.id}",
            message_data
        )
        
        print(f"[BLOG DISTRIBUTION] Successfully distributed comment {action} for blog {blog.id} "
              f"to {len(audience)} users ({online_sent} online, {offline_updated} offline)")
    
    def distribute_comment_like_update(self, blog, comment_id, action, count, user_id):
        """
        Distribute comment like updates
        """
        print(f"[BLOG DISTRIBUTION] Distributing comment like {action} for comment {comment_id}")
        
        audience = self.get_audience_for_blog(blog)
        
        message_data = {
            "type": "comment_like_update",
            "blog_id": str(blog.id),
            "comment_id": str(comment_id),
            "action": action,
            "likes_count": count,
            "user_id": user_id
        }
        
        # Send to online users
        online_sent = self.send_to_online_users(audience, message_data)
        
        # Update BlogLoad for offline users
        offline_updated = self.update_blog_load_for_offline_users(audience, blog.id, 'modified_blogs')
        
        # Send to blog-specific channel
        async_to_sync(self.channel_layer.group_send)(
            f"blog_{blog.id}",
            message_data
        )
        
        print(f"[BLOG DISTRIBUTION] Successfully distributed comment like {action} for comment {comment_id} "
              f"to {len(audience)} users ({online_sent} online, {offline_updated} offline)")
    
    @staticmethod
    def recursive_convert_objects_to_str(data):
        """
        Recursively convert UUID and datetime objects to strings for JSON serialization
        """
        import uuid
        import datetime
        
        if isinstance(data, dict):
            return {k: BlogDistributionService.recursive_convert_objects_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [BlogDistributionService.recursive_convert_objects_to_str(i) for i in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, datetime.datetime):
            return data.isoformat()
        else:
            return data