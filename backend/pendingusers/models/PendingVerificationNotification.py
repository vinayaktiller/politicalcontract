from django.db import models
from django.utils import timezone

class PendingVerificationNotification(models.Model):
    user_email = models.EmailField()
    generated_user_id = models.BigIntegerField()
    name = models.CharField(max_length=255)
    profile_pic = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'pendinguser"."pending_verification_notification'
        indexes = [
            models.Index(fields=['user_email', 'delivered']),
        ]

class PendingRejectionNotification(models.Model):
    user_email = models.EmailField()
    pending_user_id = models.BigIntegerField()
    rejection_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'pendinguser"."pending_rejection_notification'
        indexes = [
            models.Index(fields=['user_email', 'delivered']),
        ]