import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from ..models import Conversation, Message
from users.models import UserTree
import datetime

logger = logging.getLogger(__name__)
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.conversation_id = None
        self.user = None

    async def connect(self):
        try:
            self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
            
            # Extract token from query string
            query_params = self.scope['query_string'].decode()
            token_param = [p.split('=') for p in query_params.split('&') if p.startswith('token=')]
            token = token_param[0][1] if token_param else None
            
            if token:
                try:
                    access_token = AccessToken(token)
                    self.user = await self.get_user(access_token['user_id'])
                except (TokenError, KeyError, IndexError) as e:
                    logger.error(f"Token validation failed: {e}")
                    await self.close()
                    return
            
            if not self.user or not self.user.is_authenticated:
                logger.warning("Unauthenticated connection attempt")
                await self.close()
                return
                
            if not await self.validate_conversation_access():
                logger.warning(f"User {self.user.id} not in conversation {self.conversation_id}")
                await self.close()
                return
            
            self.room_group_name = f'chat_{self.conversation_id}'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"WebSocket connected: {self.user} in {self.conversation_id}")
            
            # Mark conversation as read when user connects
            await self.mark_conversation_read()

        except Exception as e:
            logger.error(f"Error during connection: {e}")
            await self.close()

    async def disconnect(self, close_code):
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected: {self.user} from {self.conversation_id}")
        else:
            logger.info(f"WebSocket disconnected without a group: {self.user}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                content = data.get('content')
                await self.handle_new_message(content)
            elif message_type == 'typing':
                await self.handle_typing_indicator()
            elif message_type == 'read_receipt':
                await self.handle_read_receipt()
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def handle_new_message(self, content):
        message = await self.save_message(content)
        
        if message:
            message_dict = await self.message_to_dict(message)
            # Broadcast to others EXCEPT sender
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_dict,
                    'sender_channel': self.channel_name  # Exclude sender
                }
            )
            # Send ACK to sender only
            await self.send(text_data=json.dumps({
                **message_dict,
                'type': 'message_ack'
            }))
            await self.update_conversation_last_message(message)

    async def chat_message(self, event):
        # Only send to clients that are not the sender
        if self.channel_name != event['sender_channel']:
            await self.send(text_data=json.dumps(event['message']))

    async def handle_read_receipt(self):
        try:
            await self.mark_conversation_read()
            
            # Broadcast read receipt to other participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'update_read_status',
                    'timestamp': datetime.datetime.now().isoformat(),
                    'sender_channel': self.channel_name  # Exclude sender
                }
            )

        except Exception as e:
            logger.error(f"Error handling read receipt: {e}")

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def validate_conversation_access(self):
        try:
            user_id = self.user.id
            return Conversation.objects.filter(
                Q(id=self.conversation_id),
                Q(participant1_id=user_id) | Q(participant2_id=user_id)
            ).exists()
        except Exception:
            return False

    @database_sync_to_async
    def save_message(self, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender_id=self.user.id,
                content=content
            )
            return message
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def update_conversation_last_message(self, message):
        conversation = Conversation.objects.get(id=self.conversation_id)
        conversation.last_message = message.content
        conversation.last_message_timestamp = message.timestamp
        conversation.last_active = message.timestamp
        conversation.save()

    @database_sync_to_async
    def mark_conversation_read(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            if conversation.participant1_id == self.user.id:
                conversation.participant1_last_read = timezone.now()
            else:
                conversation.participant2_last_read = timezone.now()
            conversation.save()
        except Exception as e:
            logger.error(f"Error updating read status: {e}")

    @database_sync_to_async
    def message_to_dict(self, message):
        try:
            user_tree = UserTree.objects.get(id=message.sender_id)
            sender = {
                'id': user_tree.id,
                'name': user_tree.name,
                'profile_pic': self.get_profile_pic_url(user_tree)
            }
        except UserTree.DoesNotExist:
            try:
                user = User.objects.get(id=message.sender_id)
                sender = {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'profile_pic': None
                }
            except User.DoesNotExist:
                logger.error(f"User not found for message sender: {message.sender_id}")
                sender = {
                    'id': message.sender_id,
                    'name': 'Unknown',
                    'profile_pic': None
                }
        
        return {
            'type': 'chat_message',
            'id': str(message.id),
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'read': message.read,
            'sender': sender,
            'is_own': message.sender_id == self.user.id
        }
        
    async def update_read_status(self, event):
        if self.channel_name != event['sender_channel']:
            await self.send(text_data=json.dumps({
                'type': 'message_read_update',
                'timestamp': event['timestamp']
            }))

    def get_profile_pic_url(self, user_tree):
        if user_tree.profilepic:
            return f"http://localhost:8000{user_tree.profilepic.url}"
        return None
