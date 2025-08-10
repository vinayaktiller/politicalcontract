from django.core.management.base import BaseCommand
from django.utils import timezone
from chat.models import Conversation, Message
from users.models import Petitioner, Circle
from django.db.models import Q
import random


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

        # Get user's circle connections bidirectionally
        circle_connections = Circle.objects.filter(
            Q(userid=user.id) | Q(otherperson=user.id)
        ).distinct()

        if not circle_connections:
            self.stdout.write(self.style.WARNING('No circle connections found'))
            return

        all_conversations = []

        # Process each connection
        for connection in circle_connections:
            # Determine connected user ID
            if str(connection.userid) == str(user_id):
                connected_user_id = connection.otherperson
            else:
                connected_user_id = connection.userid

            try:
                connected_user = Petitioner.objects.get(id=connected_user_id)
            except Petitioner.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Connected user {connected_user_id} not found, skipping'))
                continue

            # Create or get conversation with ordered participants
            conversation, created = self.get_or_create_conversation(user, connected_user)
            status_str = self.style.SUCCESS('Created') if created else self.style.NOTICE('Found')
            self.stdout.write(f"{status_str} conversation: {conversation}")

            # Track conversation for bulk status update
            all_conversations.append(conversation)

            # Create sample messages for this conversation
            self.create_sample_messages(conversation, user, connected_user)

        # Final safety: Ensure all related messages are 'read_update'
        Message.objects.filter(conversation__in=all_conversations).update(status='read_update')
        self.stdout.write(self.style.SUCCESS('All related messages forcibly set to status=read_update'))

    def get_or_create_conversation(self, user1, user2):
        """
        Create or get a Conversation instance with participant1 and participant2 ordered
        by their date_joined so the ordering is consistent.
        """
        if user1.date_joined <= user2.date_joined:
            participant1, participant2 = user1, user2
        else:
            participant1, participant2 = user2, user1

        conversation, created = Conversation.objects.get_or_create(
            participant1=participant1,
            participant2=participant2
        )
        return conversation, created

    def create_sample_messages(self, conversation, user1, user2):
        """
        Create a fixed set of sample messages alternating between user1 and user2,
        assigning the correct receiver, randomizing timestamp offsets.
        """
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
            receiver = user2 if sender == user1 else user1

            # Random time offset up to 7 days and some minutes ago
            random_offset = timezone.timedelta(
                days=random.randint(0, 7),
                minutes=random.randint(5, 300)
            )
            message_time = timezone.now() - random_offset

            Message.objects.create(
                conversation=conversation,
                sender=sender,
                receiver=receiver,
                content=content,
                timestamp=message_time,
                status='read_update'
            )
        self.stdout.write(self.style.SUCCESS(f'→ Created {len(sample_messages)} messages for conversation {conversation.id}'))
