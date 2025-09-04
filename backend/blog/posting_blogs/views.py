from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BlogCreateSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import Circle, Petitioner  # Added Petitioner import
from .blog_utils import BlogDataBuilder
from ..models import BaseBlogModel
from ..blogpage.serializers import BlogSerializer
from ..models import BlogLoad  # Added BlogLoad import


class BlogCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BlogCreateSerializer(data=request.data)
        if serializer.is_valid():
            blog = serializer.save()
            
            # Send WebSocket update
            self.send_blog_update(blog.id, request.user, request)
            print("Sent WebSocket update for new blog")
            return Response({
                'id': str(blog.id),
                'message': 'Blog created successfully',
                'type': request.data.get('type'),
                'content_type': request.data.get('content_type')
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def recursive_convert_objects_to_str(data):
        import uuid
        import datetime
        if isinstance(data, dict):
            return {k: BlogCreateAPIView.recursive_convert_objects_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [BlogCreateAPIView.recursive_convert_objects_to_str(i) for i in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, datetime.datetime):
            return data.isoformat()
        else:
            return data

    def send_blog_update(self, blog_id, user, request):
        channel_layer = get_channel_layer()
        base_blog = BaseBlogModel.objects.get(id=blog_id)
        builder = BlogDataBuilder(user, request)
        blog_data = builder.get_blog_data(base_blog)
        if not blog_data:
            print("No blog data found")
            return

        serializer = BlogSerializer(blog_data, context={'request': request})
        serialized_blog = serializer.data

        # Convert UUID and datetime to strings recursively before sending
        serialized_blog = self.recursive_convert_objects_to_str(serialized_blog)

        author_id = base_blog.userid

        circles = Circle.objects.filter(userid=author_id)
        circle_user_ids = {circle.otherperson for circle in circles if circle.otherperson}

        blog_type_parts = base_blog.type.split('_')
        blog_base_type = blog_type_parts[0]  # This gives 'journey', 'milestone', etc.

        user_ids = list(circle_user_ids) + [author_id]
        print(f"Sending to user IDs: {user_ids}, {base_blog.type, blog_base_type}")

        for uid in user_ids:
            try:
                # Check if user is online
                user_obj = Petitioner.objects.get(id=uid)
                if user_obj.is_online:
                    # Send WebSocket to online users
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{uid}",
                        {
                            "type": "blog_created",
                            "blog_id": str(blog_id),
                            "action": "blog_created",
                            'blog_type': blog_base_type,
                            "blog": serialized_blog,
                            "user_id": user.id
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
                "type": "blog_created",
                "blog_id": str(blog_id),
                "action": "blog_created",
                'blog_type': base_blog.type,
                "blog": serialized_blog,
                "user_id": user.id
            }
        )