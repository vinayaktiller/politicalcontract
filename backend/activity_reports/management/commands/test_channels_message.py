# management/commands/test_channels_message.py
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    def handle(self, *args, **options):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            "activity_today",
            {
                "type": "activity_update",
                "count": 99
            }
        )
        print("Sent test group message to 'activity_today'")
