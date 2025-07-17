# activity_reports/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from activity_reports.models import DailyActivitySummary

logger = logging.getLogger(__name__)

@receiver(post_save, sender=DailyActivitySummary, dispatch_uid="daily_activity_summary_update")
def send_activity_update(sender, instance, **kwargs):
    logger.info(f"[Signal] Received update for {instance.date}")
    today = timezone.now().date()
    if instance.date == today:
        logger.info(f"[Signal] Sending activity update for {instance.date} with {len(instance.active_users)} active users")
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "activity_today",
                {
                    "type": "activity_update",
                    "count": len(instance.active_users)
                }
            )
        except Exception as e:
            logger.error(f"[Signal Error] {e}")