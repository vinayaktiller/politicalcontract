from ..serializers.connection_notification_serializer import NotificationSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from pendingusers.serializers.pending_user_serializer import PendingUserSerializer



def delete_notification_from_connection(notification):
    channel_layer = get_channel_layer()
    serialized_data = NotificationSerializer(notification).data

    event_data = {
        "type": "notification.message",
        "delete_notification": serialized_data,
    }

    print(f"Serialized notification event: {event_data}")

    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.connection_id}",
        event_data
    )
    notification.delete()
    

    