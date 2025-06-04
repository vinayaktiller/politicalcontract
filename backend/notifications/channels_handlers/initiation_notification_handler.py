import json
import logging
from asgiref.sync import sync_to_async
from pendingusers.models.notifications import InitiationNotification

logger = logging.getLogger(__name__)

async def handle_initiation_notification(consumer, data):
    """Handles Initiation Notification logic separately."""
    message_type = data.get("messagetype")

    if message_type == "verify_user":
        await verify_user_response(consumer, data)
    elif message_type == "update_seen_status":
        await update_seen_status(consumer, data)
    else:
        raise ValueError(f"Unknown message type in initiation notification: {message_type}")

async def verify_user_response(consumer, data):
    """Handles verification of a user response."""
    notification_id = data.get("notificationId")
    response = data.get("response")

    if not notification_id or response is None:
        raise ValueError("Missing 'notificationId' or 'response' in the message")

    logger.info(f"Processing verification response: {response} for notification ID: {notification_id}")
    notification = await sync_to_async(InitiationNotification.objects.get)(id=notification_id)

    if response.lower() == "yes":
        await sync_to_async(notification.mark_as_verified)()
        logger.info(f"User {notification_id} has been verified.")
    elif response.lower() == "no":
        await sync_to_async(notification.mark_as_rejected)()
        logger.info(f"User {notification_id} was rejected.")

    await consumer.send(json.dumps({"status": "success", "message": "Verification processed"}))

async def update_seen_status(consumer, data):
    """Handles updating notification seen status."""
    notification_id = data.get("notificationId")
    seen = data.get("seen")

    if not notification_id or seen is None:
        raise ValueError("Missing 'notificationId' or 'seen' status in the message")

    logger.info(f"Marking notification {notification_id} as seen.")
    notification = await sync_to_async(InitiationNotification.objects.get)(id=notification_id)
    await sync_to_async(notification.mark_as_viewed)()

    await consumer.send(json.dumps({"status": "success", "message": "Notification marked as seen"}))
