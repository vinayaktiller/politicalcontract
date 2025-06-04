import json
import logging
from asgiref.sync import sync_to_async
from users.models.Connectionnotification import ConnectionNotification

logger = logging.getLogger(__name__)

async def handle_connection_status(consumer, data):
    """Handles connection status updates."""
    message_type = data.get("messagetype")

    if message_type == "drop":
        await drop_connection(consumer, data)
    elif message_type == "acknowledge":
        await acknowledge_connection(consumer, data)
    else:
        raise ValueError(f"Unknown message type in connection status: {message_type}")
async def drop_connection(consumer, data):
    """Handles connection drop logic."""
    notification_id = data.get("notificationId")

    if not notification_id:
        raise ValueError("Missing 'notificationId' in the message")

    logger.info(f"Dropping connection notification {notification_id}")
    notification = await sync_to_async(ConnectionNotification.objects.get)(id=notification_id)
    
    # Logic to drop the connection can be added here
    await sync_to_async(notification.mark_as_dropped)()

    await consumer.send(json.dumps({
        "status": "success",
        "message": f"Connection notification {notification_id} dropped"
    }))
async def acknowledge_connection(consumer, data):
    """Handles connection acknowledgment logic."""
    notification_id = data.get("notificationId")

    if not notification_id:
        raise ValueError("Missing 'notificationId' in the message")

    logger.info(f"Acknowledging connection notification {notification_id}")
    notification = await sync_to_async(ConnectionNotification.objects.get)(id=notification_id)
    
    # Logic to acknowledge the connection can be added here
    await sync_to_async(notification.mark_as_completed)()

    