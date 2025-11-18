from django.db import models
from django.utils import timezone
from users.models.usertree import UserTree

class RejectedPendingUser(models.Model):
    # Original pending user data
    gmail = models.EmailField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_picture = models.CharField(max_length=255, null=True, blank=True)  # Store image path
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    
    # Address information (store IDs and names for historical record)
    country_id = models.BigIntegerField(null=True)
    country_name = models.CharField(max_length=100, null=True)
    state_id = models.BigIntegerField(null=True)
    state_name = models.CharField(max_length=100, null=True)
    district_id = models.BigIntegerField(null=True)
    district_name = models.CharField(max_length=100, null=True)
    subdistrict_id = models.BigIntegerField(null=True)
    subdistrict_name = models.CharField(max_length=100, null=True)
    village_id = models.BigIntegerField(null=True)
    village_name = models.CharField(max_length=100, null=True)
    
    # Rejection details
    rejected_by = models.ForeignKey(
        UserTree, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="rejected_pending_users"
    )
    rejection_reason = models.TextField(null=True, blank=True)
    rejected_at = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    original_pending_user_id = models.BigIntegerField(null=True)  # Store original ID for reference
    event_type = models.CharField(max_length=20, default='no_event')
    is_online = models.BooleanField(default=False)

    class Meta:
        db_table = 'pendinguser"."rejected_pending_user'
        ordering = ['-rejected_at']

    def __str__(self):
        return f"Rejected: {self.gmail} by {self.rejected_by}"