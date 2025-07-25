from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import Conversation, Message
from users.models import Petitioner, Circle
from django.db.models import Q
import random
import uuid

class Command(BaseCommand):
    help = 'Populates conversations and messages for a specific user and their circle connections'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=str, help='User ID to populate chats for')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        try:
            user = Petitioner.objects.get(id=user_id)
            self.stdout.write(self.style.SUCCESS(f'Found user: {user}'))
        except Petitioner.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {user_id} not found'))
            return

        # Get circle connections (bidirectional) using ID values
        circle_connections = Circle.objects.filter(
            Q(userid=user.id) | Q(otherperson=user.id)
        ).distinct()

        if not circle_connections:
            self.stdout.write(self.style.WARNING('No circle connections found'))
            return

        # Process each connection
        for connection in circle_connections:
            # Determine connected user ID
            if str(connection.userid) == user_id:
                connected_user_id = connection.otherperson
            else:
                connected_user_id = connection.userid
            
            # Get connected user object
            try:
                connected_user = Petitioner.objects.get(id=connected_user_id)
            except Petitioner.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Connected user {connected_user_id} not found, skipping'))
                continue
            
            # Create/get conversation with proper participant ordering
            conversation, created = self.get_or_create_conversation(user, connected_user)
            status = self.style.SUCCESS('Created') if created else self.style.NOTICE('Found')
            self.stdout.write(f"{status} conversation: {conversation}")
            
            # Generate messages
            self.create_sample_messages(conversation, user, connected_user)

    def get_or_create_conversation(self, user1, user2):
        """Create conversation with participants ordered by date_joined"""
        # Determine participant order based on who joined first
        if user1.date_joined <= user2.date_joined:
            participant1, participant2 = user1, user2
        else:
            participant1, participant2 = user2, user1
            
        return Conversation.objects.get_or_create(
            participant1=participant1,
            participant2=participant2
        )

    def create_sample_messages(self, conversation, user1, user2):
        sample_messages = [
            ("Hey, how's it going?", user1),
            ("Doing well! Working on that project", user2),
            ("Need help with the database schema?", user1),
            ("Actually yes! Could you review my models?", user2),
            ("Sent you a screenshot. Thoughts?", user1),
            ("Perfect solution, thanks!", user2),
            ("When are you free for a call?", user1),
            ("How about tomorrow afternoon?", user2),
        ]

        for content, sender in sample_messages:
            # Determine receiver based on who is the other participant
            receiver = user2 if sender == user1 else user1
            
            # Create message with explicit receiver
            Message.objects.create(
                conversation=conversation,
                sender=sender,
                receiver=receiver,
                content=content,
                timestamp=timezone.now() - timezone.timedelta(
                    days=random.randint(0, 7),
                    minutes=random.randint(5, 300)
                )
            )
        self.stdout.write(self.style.SUCCESS(f'→ Created {len(sample_messages)} messages'))