# users/signals.py
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import Petitioner

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Petitioner)
@receiver(post_delete, sender=Petitioner)
def update_petitioner_count(sender, instance, **kwargs):
    try:
        total = Petitioner.objects.count()
        logger.info(f"[Signal] Sending petitioner count update: {total}")
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "user_count",
            {
                "type": "user_count_update",
                "total": total
            }
        )
    except Exception as e:
        logger.error(f"[Signal Error] {e}")