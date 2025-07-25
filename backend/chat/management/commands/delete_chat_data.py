from django.core.management.base import BaseCommand
from chat.models import Conversation, Message

class Command(BaseCommand):
    help = 'Delete all Conversation and Message records'

    def handle(self, *args, **kwargs):
        message_count = Message.objects.count()
        conversation_count = Conversation.objects.count()

        Message.objects.all().delete()
        Conversation.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(f'Deleted {message_count} messages and {conversation_count} conversations.')
        )
