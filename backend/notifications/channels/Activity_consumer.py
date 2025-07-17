import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import date
# Fixed absolute import - REPLACE 'yourapp' with your actual app name
from activity_reports.models import DailyActivitySummary

logger = logging.getLogger(__name__)

class ActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("ws/activity/today/ WebSocket connection initiated")
        self.group_name = 'activity_today'
        
        # FIRST accept the connection
        await self.accept()  # Moved this up
        logger.info("ws/activity/today/ WebSocket connection accepted")
        
        # THEN add to group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.send_initial_count()
        
    async def disconnect(self, close_code):
        logger.info(f"ws/activity/today/ WebSocket disconnected with code: {close_code}")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def activity_update(self, event):
        logger.info(f"Received activity update: {event}")
        await self.send(text_data=json.dumps({
            'count': event['count']
        }))

    async def send_initial_count(self):
        today = date.today()
        try:
            summary = await DailyActivitySummary.objects.aget(date=today)
            count = len(summary.active_users)
            logger.info(f"Initial active users count: {count}")
        except DailyActivitySummary.DoesNotExist:
            count = 0
            logger.warning("No daily activity summary found for today")
            
        await self.send(text_data=json.dumps({
            'count': count
        }))