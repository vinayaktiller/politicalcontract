# notifications/channels_handlers/milestone_handler.py
import logging
from asgiref.sync import async_to_sync
import json

logger = logging.getLogger(__name__)

async def handle_milestone_notification(consumer, data):
    """Handle milestone notifications"""
    try:
        milestone = data.get('milestone', {})
        user_id = milestone.get('user_id')
        
        logger.info(f"Received milestone notification for user {user_id}: {milestone.get('title')}")
        
        # Add any additional processing here
        # For example, update UI or trigger animations
        
    except Exception as e:
        logger.error(f"Error handling milestone notification: {str(e)}")
        await consumer.send(json.dumps({
            "error": str(e),
            "category": "error",
            "source": "milestone_handler"
        }))