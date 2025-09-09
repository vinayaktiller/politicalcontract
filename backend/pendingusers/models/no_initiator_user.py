# models.py
from django.db import models
from django.utils import timezone
from .pendinguser import PendingUser
from users.models.usertree import UserTree

class NoInitiatorUser(models.Model):
    pending_user = models.OneToOneField(PendingUser, on_delete=models.CASCADE, related_name="no_initiator_data")
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[("unclaimed", "Unclaimed"), ("claimed", "Claimed"), ("verified", "Verified"), ("spam", "Spam")],
        default="unclaimed"
    )
    claimed_by = models.ForeignKey(
        UserTree, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_no_initiators"
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        UserTree, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_no_initiators"
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pendinguser"."no_initiator_user'
    
    @property
    def is_claim_expired(self):
        if self.claimed_at:
            return (timezone.now() - self.claimed_at).total_seconds() > 24 * 3600  # 24 hours
        return False