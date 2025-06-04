import json
import logging
from asgiref.sync import sync_to_async
from users.models.Connectionnotification import ConnectionNotification

logger = logging.getLogger(__name__)

async def handle_connection_notification(consumer, data):
    """Routes connection notification messages based on message type."""
    message_type = data.get("messagetype")

    if message_type == "update_seen_status":
        await update_seen_status(consumer, data)
    elif message_type == "connection_action":
        await connection_action(consumer, data)
    
    else:
        raise ValueError(f"Unknown message type in connection notification: {message_type}")

async def update_seen_status(consumer, data):
    """Mark a connection notification as viewed by the recipient."""
    notification_id = data.get("notificationId")
    seen = data.get("seen")

    if not notification_id or seen is None:
        raise ValueError("Missing 'notificationId' or 'seen' status in the message")

    logger.info(f"Marking connection notification {notification_id} as seen: {seen}")
    notification = await sync_to_async(ConnectionNotification.objects.get)(id=notification_id)
    # Mark viewed regardless of the 'seen' flag value
    await sync_to_async(notification.mark_as_viewed)()

    await consumer.send(json.dumps({
        "status": "success",
        "message": "Connection notification marked as seen"
    }))
async def connection_action(consumer, data):
    """Handles connection actions like accept or reject."""
    notification_id = data.get("notificationNumber")
    action = data.get("action")

    if not notification_id or not action:
        raise ValueError("Missing 'notificationId' or 'action' in the message")

    logger.info(f"Processing connection action: {action} for notification ID: {notification_id}")
    notification = await sync_to_async(ConnectionNotification.objects.get)(id=notification_id)

    if action.lower() == "accept":
        await sync_to_async(notification.mark_as_accepted)()
        logger.info(f"Connection {notification_id} has been accepted.")
    elif action.lower() == "reject":
        await sync_to_async(notification.mark_as_rejected)()
        logger.info(f"Connection {notification_id} was rejected.")
    else:
        raise ValueError(f"Unknown action type: {action}")

    await consumer.send(json.dumps({
        "status": "success",
        "message": f"Connection action '{action}' processed"
    }))
