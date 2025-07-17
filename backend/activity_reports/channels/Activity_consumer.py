# activity_reports/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import date
from activity_reports.models import DailyActivitySummary
from users.models import Petitioner

logger = logging.getLogger(__name__)

class ActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            logger.info("ws/activity/today/ WebSocket connection initiated")
            self.groups = ['activity_today', 'user_count']
            
            await self.accept()
            logger.info("ws/activity/today/ WebSocket connection accepted")
            
            # Add to both groups
            for group in self.groups:
                await self.channel_layer.group_add(
                    group,
                    self.channel_name
                )
            
            await self.send_initial_counts()
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        logger.info(f"ws/activity/today/ WebSocket disconnected with code: {close_code}")
        for group in self.groups:
            await self.channel_layer.group_discard(
                group,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON data")

    async def activity_update(self, event):
        """Handle updates from activity_today group"""
        logger.info(f"Received activity update: {event}")
        await self.send(text_data=json.dumps({
            'update_type': 'active_users',
            'count': event.get('count', 0)
        }))

    async def user_count_update(self, event):
        """Handle updates from user_count group"""
        logger.info(f"Received petitioner update: {event}")
        await self.send(text_data=json.dumps({
            'update_type': 'petitioners',
            'count': event.get('total', 0)
        }))

    async def send_initial_counts(self):
        today = date.today()
        active_count = 0
        petitioners_count = 0
        
        try:
            summary = await DailyActivitySummary.objects.aget(date=today)
            active_count = len(summary.active_users)
            logger.info(f"Initial active users count: {active_count}")
        except DailyActivitySummary.DoesNotExist:
            logger.warning("No daily activity summary found for today")
        except Exception as e:
            logger.error(f"Error fetching daily summary: {str(e)}")
        
        try:
            petitioners_count = await Petitioner.objects.acount()
            logger.info(f"Initial petitioners count: {petitioners_count}")
        except Exception as e:
            logger.error(f"Error fetching petitioners count: {str(e)}")
            
        await self.send(text_data=json.dumps({
            'update_type': 'active_users',
            'count': active_count
        }))
        await self.send(text_data=json.dumps({
            'update_type': 'petitioners',
            'count': petitioners_count
        }))