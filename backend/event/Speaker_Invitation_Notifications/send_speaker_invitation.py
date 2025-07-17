# notifications/services/send_speaker_invitation.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .speaker_invitation_serializer import SpeakerInvitationSerializer

def send_speaker_invitation(notification):
    channel_layer = get_channel_layer()
    serialized_data = SpeakerInvitationSerializer(notification).data

    event_data = {
        "type": "notification.message",
        "notification": serialized_data,
    }

    print(f"Serialized speaker invitation event: {event_data} to user {notification.speaker.id}")

    async_to_sync(channel_layer.group_send)(
        f"notifications_{notification.speaker.id}",
        event_data
    )