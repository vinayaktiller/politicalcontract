from django.db import models, transaction
from django.utils.timezone import now
from .groups import Group
from users.models.petitioners import Petitioner
import logging

logger = logging.getLogger(__name__)

class GroupSpeakerInvitationNotification(models.Model):
    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    STATUS_MESSAGES = {
        Status.INVITED: "🎤 You've been invited to be a speaker in {group_name}",
        Status.ACCEPTED: "✅ You accepted the speaker role in {group_name}",
        Status.REJECTED: "❌ You declined the speaker role in {group_name}"
    }

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="speaker_invitations")
    speaker = models.ForeignKey(Petitioner, on_delete=models.CASCADE, related_name="group_speaker_invitations")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INVITED)
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)  # New field to track freshness

    class Meta:
        db_table = 'event"."groupspeakerinvitationnotification'
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["speaker", "status"]),
            models.Index(fields=["seen"]),  # Index added for efficient query lookup
        ]

    def __str__(self):
        return f"SpeakerInvitation for {self.speaker} in {self.group} - Status: {self.status}, Seen: {self.seen}"

    def get_status_message(self):
        return self.STATUS_MESSAGES[self.status].format(group_name=self.group.name)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new:
            self.send_invitation_notification()

    def send_invitation_notification(self):
        from ..Speaker_Invitation_Notifications.send_speaker_invitation import send_speaker_invitation
        send_speaker_invitation(self)

    def mark_as_seen(self):
        """Mark the notification as seen."""
        self.seen = True
        self.save(update_fields=["seen"])

    def mark_as_accepted(self):
        with transaction.atomic():
            self.status = self.Status.ACCEPTED
            self.save(update_fields=["status"])
            
            # Add to actual speakers
            self.group.add_speaker(self.speaker.id)
            
            # Remove from pending speakers
            if self.speaker.id in self.group.pending_speakers:
                self.group.pending_speakers.remove(self.speaker.id)
                self.group.save(update_fields=['pending_speakers'])

            self.delete()  # Remove the invitation notification

    def mark_as_rejected(self):
        with transaction.atomic():
            self.status = self.Status.REJECTED
            self.save(update_fields=["status"])
            
            # Remove from pending speakers
            if self.speaker.id in self.group.pending_speakers:
                self.group.pending_speakers.remove(self.speaker.id)
                self.group.save(update_fields=['pending_speakers'])
            
            self.delete()  # Remove the invitation notification
    