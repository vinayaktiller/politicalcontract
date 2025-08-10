import json
import logging
from asgiref.sync import sync_to_async
from chat.models import Message
from users.models import Petitioner

logger = logging.getLogger(__name__)

async def handle_chat_system(consumer, data):
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
    elif action == "send_message":
        await handle_send_message(consumer, data)
    elif action == "update_message_status":
        await update_message_status(consumer, data)
    else:
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": f"Unknown chat system action: {action}"
        }))

async def handle_send_message(consumer, data):
    try:
        conversation_id = data.get("conversation_id")
        content = data.get("content")
        temp_id = data.get("temp_id")

        message = await sync_to_async(Message.objects.create)(
            conversation_id=conversation_id,
            sender_id=consumer.user_id,
            content=content
        )
        # Try to deliver immediately (if possible)
        await sync_to_async(message.try_deliver)()
        await consumer.send(json.dumps({
            "type": "notification_message",
            "category": "chat_system",
            "subtype": "message_sent",
            "message_id": str(message.id),
            "temp_id": temp_id,
            "conversation_id": conversation_id,
            "content": content,
            "timestamp": message.timestamp.isoformat(),
            "status": message.status
        }))
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": str(e),
            "temp_id": data.get("temp_id")
        }))

async def mark_message_as_read(consumer, message_id, user_id):
    try:
        message = await sync_to_async(Message.objects.get)(id=message_id)
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
    # For backward compatibility (use status instead)
    try:
        message = await sync_to_async(Message.objects.get)(id=message_id)
        # Only receiver can confirm delivery
        if str(message.receiver_id) == user_id and message.status != "delivered":
            await sync_to_async(message.update_status)("delivered")
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

async def update_message_status(consumer, data):
    """
    Update message status based on client confirmation.
    This function supports all transitions and cascading “_update” notification logic.
    """
    try:
        message_id = data.get("message_id")
        new_status = data.get("status")
        user_id = consumer.user_id

        message = await sync_to_async(Message.objects.get)(id=message_id)

        # Permissions
        valid_sender_update = str(message.sender_id) == user_id and new_status in ['delivered_update', 'read_update']
        valid_receiver_update = str(message.receiver_id) == user_id and new_status in ['delivered', 'read']

        if not (valid_sender_update or valid_receiver_update):
            raise PermissionError("Unauthorized status update")

        # Status logic and cascading rules
        if new_status == 'delivered':
            await sync_to_async(message.update_status)('delivered')
            if getattr(message.sender, "is_online", False):
                await sync_to_async(message.update_status)('delivered_update')
        elif new_status == 'delivered_update':
            await sync_to_async(message.update_status)('delivered_update')
        elif new_status == 'read':
            await sync_to_async(message.update_status)('read')
            if getattr(message.sender, "is_online", False):
                await sync_to_async(message.update_status)('read_update')
        elif new_status == 'read_update':
            await sync_to_async(message.update_status)('read_update')
        else:
            raise ValueError("Unsupported status")

        await consumer.send(json.dumps({
            "status": "success",
            "category": "chat_system",
            "action": "status_updated",
            "message_id": message_id,
            "new_status": new_status
        }))
    except Message.DoesNotExist:
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": "Message not found"
        }))
    except Exception as e:
        logger.error(f"Status update error: {str(e)}")
        await consumer.send(json.dumps({
            "status": "error",
            "category": "chat_system",
            "message": str(e)
        }))

async def handle_user_online(consumer, user_id):
    """Handle user coming online - deliver pending messages and pending status updates"""
    try:
        user = await sync_to_async(Petitioner.objects.get)(id=user_id)
        user.is_online = True
        await sync_to_async(user.save)(update_fields=["is_online"])

        # Deliver any messages as receiver
        await deliver_pending_messages(consumer, user)
        # Send pending status updates (as sender)
        await process_pending_status_updates(consumer, user)

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
    """Deliver all pending messages (as receiver)"""
    try:
        # 'sent' means not yet delivered
        pending_messages = await sync_to_async(list)(
            Message.objects.filter(receiver=user, status='sent')
        )
        for message in pending_messages:
            await sync_to_async(message.try_deliver)()
        # Optionally, re-send unread/delayed messages
    except Exception as e:
        logger.error(f"Error delivering pending messages: {str(e)}")

async def process_pending_status_updates(consumer, user):
    """Send pending status updates (as sender) when user returns online"""
    try:
        delivered_messages = await sync_to_async(list)(
            Message.objects.filter(sender=user, status='delivered')
        )
        for message in delivered_messages:
            await sync_to_async(message.update_status)('delivered_update')

        read_messages = await sync_to_async(list)(
            Message.objects.filter(sender=user, status='read')
        )
        for message in read_messages:
            await sync_to_async(message.update_status)('read_update')

    except Exception as e:
        logger.error(f"Error processing status updates: {str(e)}")

async def fetch_undelivered_messages(consumer, user_id):
    """Fetch and deliver undelivered messages for this user (receiver)"""
    try:
        user = await sync_to_async(Petitioner.objects.get)(id=user_id)
        await deliver_pending_messages(consumer, user)
    except Exception as e:
        logger.error(f"Error fetching undelivered messages: {str(e)}")

# (Optionally: helper functions for sending notifications to clients)
