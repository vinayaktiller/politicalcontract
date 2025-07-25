from django.db import models
from django.core.exceptions import ValidationError
import uuid
from django.db.models import Q
from django.utils import timezone
from users.models import Petitioner, Circle, UserTree

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant1 = models.ForeignKey(
        Petitioner, 
        on_delete=models.CASCADE,
        related_name='conversations_as_p1'
    )
    participant2 = models.ForeignKey(
        Petitioner, 
        on_delete=models.CASCADE,
        related_name='conversations_as_p2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    last_message = models.TextField(null=True, blank=True)
    last_message_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['participant1', 'participant2'], 
                name='unique_conversation'
            )
        ]
        db_table = 'chat"."conversation'

    def clean(self):
        # Ensure users are connected via Circle relationship
        if not Circle.objects.filter(
            Q(userid=self.participant1_id, otherperson=self.participant2_id) |
            Q(userid=self.participant2_id, otherperson=self.participant1_id)
        ).exists():
            raise ValidationError("Users must be connected via Circle to start a conversation")

    def save(self, *args, **kwargs):
        # Reorder participants based on date_joined to ensure consistency
        try:
            p1 = Petitioner.objects.get(id=self.participant1_id)
            p2 = Petitioner.objects.get(id=self.participant2_id)
            if p1.date_joined > p2.date_joined:
                self.participant1, self.participant2 = self.participant2, self.participant1
        except Petitioner.DoesNotExist:
            pass  # Allow save to raise error via clean() or FK constraints

        # Set initial last_active if not already set
        if not self.last_active:
            self.last_active = timezone.now()

        self.full_clean()  # Enforce validation
        super().save(*args, **kwargs)

    def update_last_message(self, message):
        """Update conversation with last message info"""
        self.last_message = message.content
        self.last_message_timestamp = message.timestamp
        self.save(update_fields=['last_message', 'last_message_timestamp'])

    def __str__(self):
        return f"Chat between {self.participant1} and {self.participant2}"

    def get_other_user(self, current_user):
        """Get the other participant with ID comparison"""
        if self.participant1_id == current_user.id:
            return self.participant2
        return self.participant1

    def get_user_profile(self, user_id):
        """Get profile from cache or fetch directly"""
        if hasattr(self, 'prefetched_profiles'):
            return self.prefetched_profiles.get(user_id)
        try:
            return UserTree.objects.get(id=user_id)
        except UserTree.DoesNotExist:
            return None
