import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q
from django.http import HttpRequest

# Import your notification/chat handlers
from notifications.channels_handlers.initiation_notification_handler import handle_initiation_notification
from notifications.channels_handlers.connection_notification_handler import handle_connection_notification
from notifications.channels_handlers.connection_status_handler import handle_connection_status
from notifications.channels_handlers.speaker_invitation_handler import handle_speaker_invitation
from notifications.channels_handlers.chat_system_handler import handle_chat_system
from notifications.channels_handlers.milestone_handler import handle_milestone_notification
from notifications.login_push.services.push_notifications import handle_user_notifications_on_login

from users.models import Circle
from blog.models import BlogLoad, BaseBlogModel
from blog.posting_blogs.blog_utils import BlogDataBuilder  # Fixed import
from blog.blogpage.serializers import BlogSerializer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for handling real-time notifications, chat events, blog updates, and milestones."""

    async def connect(self):
        """Handles WebSocket connection."""
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"notifications_{self.user_id}"
        logger.info(f"User {self.user_id} connected to WebSocket.")

        # Add to notification group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Mark user as online
        await self.mark_user_online(True)

        # Send pending notifications
        # Resolve the scope user (which may be a channels.auth.UserLazyObject) to
        # the application's Petitioner model instance before processing. This
        # prevents passing a UserLazyObject into code that expects a Petitioner
        # or a numeric id (which caused "Field 'id' expected a number" errors).
        from users.models import Petitioner
        try:
            petitioner = await sync_to_async(Petitioner.objects.get)(id=self.user_id)
        except Exception as e:
            logger.error(f"Failed to fetch Petitioner {self.user_id} for notifications: {e}")
            petitioner = None

        await sync_to_async(handle_user_notifications_on_login)(petitioner)

        # Send pending blogs
        await self.send_pending_new_blogs()
        
        # Send modified blogs
        await self.send_pending_modified_blogs()
        
        # Remove deleted blogs
        await self.remove_deleted_blogs()

        # Fetch undelivered messages
        await self.fetch_undelivered_messages()

        # Fetch undelivered milestones
        await self.fetch_undelivered_milestones()

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"User {self.user_id} disconnected from WebSocket.")

        # Mark user as offline
        await self.mark_user_online(False)

    async def mark_user_online(self, online):
        """Update user's online status and notify connections."""
        try:
            from users.models import Petitioner
            user = await sync_to_async(Petitioner.objects.get)(id=self.user_id)
            user.is_online = online
            await sync_to_async(user.save)(update_fields=['is_online'])

            # Notify user's connections about status change
            await self.notify_connection_status(online)
        except Exception as e:
            logger.error(f"Error updating online status: {str(e)}")

    async def notify_connection_status(self, online):
        """Notify user's connections about online/offline status change."""
        try:
            connections = await sync_to_async(list)(
                Circle.objects.filter(
                    Q(userid=self.user_id) | Q(otherperson=self.user_id)
                ).distinct()
            )
            for connection in connections:
                other_id = (
                    connection.userid if str(connection.userid) != str(self.user_id)
                    else connection.otherperson
                )
                group_name = f"notifications_{other_id}"

                await self.channel_layer.group_send(
                    group_name,
                    {
                        "type": "notification_message",
                        "category": "connection_status",
                        "user_id": self.user_id,
                        "online": online,
                        "timestamp": timezone.now().isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Error notifying connection status: {str(e)}")

    async def fetch_undelivered_messages(self):
        """Fetch undelivered messages for the user."""
        try:
            await self.send(json.dumps({
                "category": "chat_system",
                "action": "fetch_undelivered"
            }))
        except Exception as e:
            logger.error(f"Error fetching undelivered messages: {str(e)}")

    async def fetch_undelivered_milestones(self):
        """Fetch undelivered milestones for the user"""
        try:
            from users.models import Milestone  # avoid circular import

            milestones = await sync_to_async(list)(
                Milestone.objects.filter(user_id=self.user_id, delivered=False)
            )
            for milestone in milestones:
                await self.send_milestone_notification(milestone)

                milestone.delivered = True
                await sync_to_async(milestone.save)(update_fields=['delivered'])
        except Exception as e:
            logger.error(f"Error fetching undelivered milestones: {str(e)}")

    async def send_milestone_notification(self, milestone):
        """Send milestone notification to client"""
        notification = {
            "notification_type": "Milestone_Notification",
            "notification_message": f"Achievement unlocked: {milestone.title}",
            "notification_data": {
                "milestone_id": str(milestone.id),
                "user_id": milestone.user_id,
                "title": milestone.title,
                "text": milestone.text,
                "created_at": milestone.created_at.isoformat(),
                "delivered": milestone.delivered,
                "photo_id": milestone.photo_id,
                "photo_url": milestone.photo_url,
                "type": milestone.type
            },
            "notification_number": str(milestone.id),
            "notification_freshness": True,
            "created_at": milestone.created_at.isoformat()
        }

        await self.send(json.dumps({
            "notification": notification
        }))

    async def receive(self, text_data):
        """Handles incoming WebSocket messages and delegates processing."""
        try:
            data = json.loads(text_data)
            category = data.get("category")

            # Handle blog updates
            if category == "blog_update":
                await self.handle_blog_update(data)

            # Handle milestone notifications
            elif category == "milestone":
                await handle_milestone_notification(self, data)

            # Handle chat system events
            elif category == "chat_system":
                await handle_chat_system(self, data)

            # Handle message status update category separately
            elif category == "message_status_update":
                await self.handle_message_status_update(data)

            # Other notification types
            elif data.get("notificationType") == "Initiation_Notification":
                await handle_initiation_notification(self, data)
            elif data.get("notificationType") == "Connection_Notification":
                await handle_connection_notification(self, data)
            elif data.get("notificationType") == "Connection_Status":
                await handle_connection_status(self, data)
            elif data.get("notificationType") == "Group_Speaker_Invitation":
                await handle_speaker_invitation(self, data)

            elif data.get("notificationType") == "Milestone_Notification":
                pass
            elif data.get("action") == "delete_notification":
                pass
            else:
                raise ValueError(f"Unknown message category: {category or 'no category'} data: {data}")

        except json.JSONDecodeError:
            logger.error(f"JSON decoding error from user {self.user_id}: {text_data}")
            await self.send(json.dumps({
                "error": "Invalid JSON format",
                "category": "error"
            }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(json.dumps({
                "error": str(e),
                "category": "error",
                "source": "receive_handler"
            }))

    async def handle_blog_update(self, data):
        """Handle blog update messages"""
        action = data.get("action")

        if action == "subscribe_to_blog":
            blog_id = data.get("blog_id")
            await self.channel_layer.group_add(f"blog_{blog_id}", self.channel_name)

        elif action == "unsubscribe_from_blog":
            blog_id = data.get("blog_id")
            await self.channel_layer.group_discard(f"blog_{blog_id}", self.channel_name)

    async def handle_message_status_update(self, data):
        """Handle client-side message status updates."""
        try:
            message_id = data.get("message_id")
            new_status = data.get("status")

            valid_statuses = ['sent', 'delivered', 'delivered_update', 'read', 'read_update']
            if new_status not in valid_statuses:
                raise ValueError("Invalid message status")

            await handle_chat_system(self, {
                "action": "update_message_status",
                "message_id": message_id,
                "status": new_status,
                "category": "chat_system"
            })

        except Exception as e:
            logger.error(f"Status update handling error: {str(e)}")
            await self.send(json.dumps({
                "status": "error",
                "category": "message_status_update",
                "message": str(e)
            }))

    async def notification_message(self, event):
        """Sends notifications to the WebSocket client with category filtering."""
        event.setdefault('category', 'general')

        logger.info(f"Sending notification to user {self.user_id}: {event}")
        await self.send(text_data=json.dumps(event))

    async def blog_update(self, event):
        """Sends blog updates to the WebSocket client"""
        await self.send(text_data=json.dumps(event))

    async def comment_update(self, event):
        """Sends comment updates to the WebSocket client"""
        await self.send(text_data=json.dumps(event))

    async def comment_like_update(self, event):
        """Sends comment like updates to the WebSocket client"""
        await self.send(text_data=json.dumps(event))

    async def reply_update(self, event):
        """Sends reply updates to the WebSocket client"""
        await self.send(text_data=json.dumps(event))

    async def blog_created(self, event):
        """Sends blog creation updates to the WebSocket client"""
        print("Sending blog creation update to WebSocket client")
        await self.send(text_data=json.dumps({
            "type": "blog_created",
            "blog_id": event["blog_id"],
            "action": event["action"],
            "blog_type": event["blog_type"],
            "blog": event["blog"],
            "user_id": event["user_id"]
        }))

    async def blog_modified(self, event):
        """Sends blog modification updates to the WebSocket client"""
        print("Sending blog modification update to WebSocket client")
        await self.send(text_data=json.dumps({
            "type": "blog_modified",
            "blog_id": event["blog_id"],
            "action": event["action"],
            "blog": event["blog"],
            "user_id": event["user_id"]
        }))

    async def blog_shared(self, event):
        """Sends blog share updates to the WebSocket client"""
        print("Sending blog share update to WebSocket client")
        await self.send(text_data=json.dumps({
            "type": "blog_shared",
            "blog_id": event["blog_id"],
            "action": event["action"],
            "blog": event["blog"],
            "shared_by_user_id": event["shared_by_user_id"],
            "original_author_id": event["original_author_id"],
            "user_id": event["user_id"]
        }))

    async def blog_unshared(self, event):
        """Sends blog unshare updates to the WebSocket client"""
        print("Sending blog unshare update to WebSocket client")
        
        # Ensure all IDs are strings and consistent
        blog_id = str(event.get("blog_id"))
        shared_by_user_id = str(event.get("shared_by_user_id"))
        original_author_id = str(event.get("original_author_id"))
        user_id = str(event.get("user_id"))
        
        unshare_data = {
            "type": "blog_unshared",
            "blog_id": blog_id,
            "action": "unshared",  # Changed from event["action"] to consistent "unshared"
            "shared_by_user_id": shared_by_user_id,
            "original_author_id": original_author_id,
            "user_id": user_id,
            "shares_count": event.get("shares_count", 0)
        }
        
        print(f"[WEBSOCKET] Sending blog_unshared: {unshare_data}")
        await self.send(text_data=json.dumps(unshare_data))

    # -----------------------------
    # ✅ Pending Blog Senders
    # -----------------------------
    
    async def send_pending_new_blogs(self):
        """Check for new blogs in BlogLoad and send them to the user"""
        try:
            blog_load = await sync_to_async(
                BlogLoad.objects.filter(userid=self.user_id).first
            )()

            if blog_load and blog_load.new_blogs:
                logger.info(f"Found {len(blog_load.new_blogs)} new blogs for user {self.user_id}")

                request = HttpRequest()
                request.method = 'GET'
                request.user = self.scope.get('user', None)

                # Add required META keys to avoid SERVER_NAME error
                request.META['SERVER_NAME'] = 'localhost'
                request.META['SERVER_PORT'] = '8000'
                request.META['HTTP_HOST'] = 'localhost:8000'

                from users.models import Petitioner
                user_obj = await sync_to_async(Petitioner.objects.get)(id=self.user_id)

                # Make a copy of new_blogs to iterate safely while modifying original list
                new_blogs_copy = list(blog_load.new_blogs)

                for blog_id in new_blogs_copy:
                    try:
                        base_blog = await sync_to_async(BaseBlogModel.objects.get)(id=blog_id)
                        builder = BlogDataBuilder(user_obj, request)
                        blog_data = await sync_to_async(builder.get_blog_data)(base_blog)

                        if blog_data:
                            serializer = BlogSerializer(blog_data, context={'request': request})
                            serialized_blog = serializer.data
                            serialized_blog = self.recursive_convert_objects_to_str(serialized_blog)

                            await self.send(text_data=json.dumps({
                                "type": "blog_created",
                                "blog_id": str(blog_id),
                                "action": "blog_created",
                                "blog_type": base_blog.type.split('_')[0],
                                "blog": serialized_blog,
                                "user_id": str(base_blog.userid)
                            }))

                            logger.info(f"Sent pending blog {blog_id} to user {self.user_id}")

                            # Remove the blog_id from new_blogs after successfully sending
                            blog_load.new_blogs.remove(blog_id)
                            await sync_to_async(blog_load.save)()

                    except BaseBlogModel.DoesNotExist:
                        logger.warning(f"Blog {blog_id} not found, skipping")
                        # Remove invalid blog_id to avoid retrying endlessly
                        blog_load.new_blogs.remove(blog_id)
                        await sync_to_async(blog_load.save)()
                        continue

        except Exception as e:
            logger.error(f"Error sending pending new blogs: {str(e)}")
            
    async def send_pending_modified_blogs(self):
        """Check for modified blogs in BlogLoad and send them to the user"""
        try:
            blog_load = await sync_to_async(
                BlogLoad.objects.filter(userid=self.user_id).first
            )()

            if blog_load and blog_load.modified_blogs:
                logger.info(f"Found {len(blog_load.modified_blogs)} modified blogs for user {self.user_id}")

                request = HttpRequest()
                request.method = 'GET'
                request.user = self.scope.get('user', None)

                # Add required META keys to avoid SERVER_NAME error
                request.META['SERVER_NAME'] = 'localhost'
                request.META['SERVER_PORT'] = '8000'
                request.META['HTTP_HOST'] = 'localhost:8000'

                from users.models import Petitioner
                user_obj = await sync_to_async(Petitioner.objects.get)(id=self.user_id)

                # Make a copy of modified_blogs to iterate safely while modifying original list
                modified_blogs_copy = list(blog_load.modified_blogs)

                for blog_id in modified_blogs_copy:
                    try:
                        base_blog = await sync_to_async(BaseBlogModel.objects.get)(id=blog_id)
                        builder = BlogDataBuilder(user_obj, request)
                        blog_data = await sync_to_async(builder.get_blog_data)(base_blog)

                        if blog_data:
                            serializer = BlogSerializer(blog_data, context={'request': request})
                            serialized_blog = serializer.data
                            serialized_blog = self.recursive_convert_objects_to_str(serialized_blog)

                            await self.send(text_data=json.dumps({
                                "type": "blog_modified",
                                "blog_id": str(blog_id),
                                "action": "blog_modified",
                                "blog": serialized_blog,
                                "user_id": str(base_blog.userid)
                            }))

                            logger.info(f"Sent modified blog {blog_id} to user {self.user_id}")

                            # Remove the blog_id from modified_blogs after successfully sending
                            blog_load.modified_blogs.remove(blog_id)
                            await sync_to_async(blog_load.save)()

                    except BaseBlogModel.DoesNotExist:
                        logger.warning(f"Blog {blog_id} not found, skipping")
                        # Remove invalid blog_id to avoid retrying endlessly
                        blog_load.modified_blogs.remove(blog_id)
                        await sync_to_async(blog_load.save)()
                        continue

        except Exception as e:
            logger.error(f"Error sending pending modified blogs: {str(e)}")

    async def remove_deleted_blogs(self):
        """Check for deleted blogs in BlogLoad and send removal commands to the client"""
        try:
            blog_load = await sync_to_async(
                BlogLoad.objects.filter(userid=self.user_id).first
            )()

            if blog_load and blog_load.deleted_blogs:
                logger.info(f"Found {len(blog_load.deleted_blogs)} deleted blogs for user {self.user_id}")

                # Make a copy of deleted_blogs to iterate safely while modifying original list
                deleted_blogs_copy = list(blog_load.deleted_blogs)

                for blog_id in deleted_blogs_copy:
                    await self.send(text_data=json.dumps({
                        "type": "blog_deleted",
                        "blog_id": str(blog_id),
                        "action": "blog_deleted"
                    }))

                    logger.info(f"Sent blog deletion for {blog_id} to user {self.user_id}")

                    # Remove the blog_id from deleted_blogs after successfully sending
                    blog_load.deleted_blogs.remove(blog_id)
                    await sync_to_async(blog_load.save)()

        except Exception as e:
            logger.error(f"Error removing deleted blogs: {str(e)}")

    @staticmethod
    def recursive_convert_objects_to_str(data):
        """Recursively convert UUID and datetime objects to strings"""
        import uuid
        import datetime
        if isinstance(data, dict):
            return {k: NotificationConsumer.recursive_convert_objects_to_str(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [NotificationConsumer.recursive_convert_objects_to_str(i) for i in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, datetime.datetime):
            return data.isoformat()
        else:
            return data