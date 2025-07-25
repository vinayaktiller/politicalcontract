import json
import logging
from asgiref.sync import sync_to_async
from chat.models import Message, Conversation
from users.models import Petitioner

logger = logging.getLogger(__name__)

async def handle_chat_system(consumer, data):
    """Handle chat-related system events"""
    action = data.get("action")
    message_id = data.get("message_id")
    user_id = consumer.user_id
    
    if action == "mark_as_read":
        await mark_message_as_read(consumer, message_id, user_id)
    elif action == "confirm_delivery":
        await confirm_message_delivery(consumer, message_id, user_id)
    elif action == "user_online":
        await handle_user_online(consumer, user_id)
    elif action == "fetch_undelivered":
        await fetch_undelivered_messages(consumer, user_id)
    else:
        raise ValueError(f"Unknown chat system action: {action}")

async def mark_message_as_read(consumer, message_id, user_id):
    """Mark a message as read"""
    try:
        message = await sync_to_async(Message.objects.get)(id=message_id)
        
        # Verify current user is the receiver
        if str(message.receiver_id) == user_id:
            await sync_to_async(message.mark_as_read)()
            await consumer.send(json.dumps({
                "status": "success",
                "category": "chat_system",
                "action": "read_confirmed",
                "message_id": message_id
            }))
        else:
            await consumer.send(json.dumps({
                "status": "error",
                "category": "chat_system",
                "message": "Not authorized to mark this message as read",
                "message_id": message_id
            }))
    except Message.DoesNotExist:
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": "Message not found",
            "message_id": message_id
        }))
    except Exception as e:
        logger.error(f"Error marking message as read: {str(e)}")
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": str(e),
            "message_id": message_id
        }))

async def confirm_message_delivery(consumer, message_id, user_id):
    """Confirm message delivery (client-side confirmation)"""
    try:
        message = await sync_to_async(Message.objects.get)(id=message_id)
        
        # Verify current user is the receiver
        if str(message.receiver_id) == user_id and not message.delivered:
            message.delivered = True
            await sync_to_async(message.save)(update_fields=['delivered'])
                
        await consumer.send(json.dumps({
            "status": "success",
            "category": "chat_system",
            "action": "delivery_confirmed",
            "message_id": message_id
        }))
    except Message.DoesNotExist:
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": "Message not found",
            "message_id": message_id
        }))
    except Exception as e:
        logger.error(f"Error confirming message delivery: {str(e)}")
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": str(e),
            "message_id": message_id
        }))

async def handle_user_online(consumer, user_id):
    """Handle user coming online - deliver pending messages and update status"""
    try:
        user = await sync_to_async(Petitioner.objects.get)(id=user_id)
        
        # Mark user as online
        user.is_online = True
        await sync_to_async(user.save)(update_fields=['is_online'])
        
        # Deliver pending messages
        await deliver_pending_messages(consumer, user)
        
        # Notify about online status
        await consumer.send(json.dumps({
            "status": "success",
            "category": "chat_system",
            "action": "online_status_updated",
            "online": True
        }))
    except Exception as e:
        logger.error(f"Error handling user online: {str(e)}")
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": str(e)
        }))

async def deliver_pending_messages(consumer, user):
    """Deliver all pending messages for a user"""
    try:
        # Get undelivered messages
        pending_messages = await sync_to_async(list)(
            Message.objects.filter(receiver=user, delivered=False)
        )
        
        # Deliver each message
        for message in pending_messages:
            await sync_to_async(message.try_deliver)()
            
        # Get unread messages
        unread_messages = await sync_to_async(list)(
            Message.objects.filter(receiver=user, read=False)
        )
        
        # Send unread messages to client
        for message in unread_messages:
            await send_message_to_client(consumer, message)
            
    except Exception as e:
        logger.error(f"Error delivering pending messages: {str(e)}")

async def send_message_to_client(consumer, message):
    """Send message to client via WebSocket"""
    try:
        await consumer.send(json.dumps({
            "type": "notification_message",
            "category": "chat_system",
            "subtype": "new_message",
            "message_id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "content": message.content,
            "sender_id": str(message.sender_id),
            "timestamp": message.timestamp.isoformat()
        }))
    except Exception as e:
        logger.error(f"Failed to send message to client: {str(e)}")

async def fetch_undelivered_messages(consumer, user_id):
    """Fetch undelivered messages when client reconnects"""
    try:
        user = await sync_to_async(Petitioner.objects.get)(id=user_id)
        await deliver_pending_messages(consumer, user)
    except Exception as e:
        logger.error(f"Error fetching undelivered messages: {str(e)}")