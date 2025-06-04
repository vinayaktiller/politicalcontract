import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from ..serializers.NotificationSerializer import NotificationSerializer

# Configure logger
logger = logging.getLogger(__name__)

def send_notification_to_initiator(notification):
    channel_layer = get_channel_layer()
    serialized_data = NotificationSerializer(notification).data

    # Log and print notification details before sending
    logger.info(f"Notification Object: {notification}")
    logger.info(f"Serialized Notification Data: {serialized_data}")
    print(f"Notification Object: {notification}")
    print(f"Serialized Notification Event: {serialized_data}")

    event_data = {
        "type": "notification.message",
        "notification": serialized_data,
    }

    try:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{notification.initiator_id}",  # Keeping as-is per your request
            event_data
        )
        logger.info(f"Notification successfully sent to: notifications_{notification.initiator_id}")
    except Exception as e:
        logger.error(f"Error sending WebSocket notification for initiator {notification.initiator_id}: {str(e)}")

# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# from pendingusers.serializers.pending_user_serializer import PendingUserSerializer
# from ..serializers.NotificationSerializer import NotificationSerializer

# def send_notification_to_initiator(notification):
#     channel_layer = get_channel_layer()
#     serialized_data = NotificationSerializer(notification).data

#     event_data = {
#         "type": "notification.message",
#         "notification": serialized_data,
#     }

#     print(f"Serialized notification event: {event_data}")

#     async_to_sync(channel_layer.group_send)(
#         f"notifications_{notification.initiator_id}",
#         event_data
#     )
    
# def send_notification_to_initiator(notification):
#     applicant_data = PendingUserSerializer(notification.applicant).data
#     channel_layer = get_channel_layer()
#     event_data = {
#         "type": "notification.message",
#         "notification": {
#             "notification_type": "initiation notification",
#             "notification_freshness": notification.viewed,
#             "notification_message": f"Are you initiating {notification.applicant.first_name} {notification.applicant.last_name}?",
#             "notification_data": applicant_data,
#             "notification_number": notification.id
#         }
#     }
#     print(f"Event data being sent: {event_data}")
#     async_to_sync(channel_layer.group_send)(
#         f"notifications_{notification.initiator_id}",
#         event_data
#     )
