from ..serializers.connection_status_serializer import ConnectionStatusSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_status_to_applicant(notification):
    channel_layer = get_channel_layer()
    serialized_data = ConnectionStatusSerializer(notification).data

    event_data = {
        "type": "notification.message",
        "notification": serialized_data,
    }

    print(f"Serialized status event from send_status_to_applicant: {event_data} to applicant {notification.applicant_id}")

    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.applicant_id}",
        event_data
    )
