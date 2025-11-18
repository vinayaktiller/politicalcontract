from django.db import models
from django.utils import timezone
from geographies.models.geos import Country, State, District, Subdistrict, Village

class NoInitiatorVerificationHistory(models.Model):
    # Original PendingUser data (who originally had no initiator)
    original_pending_user_id = models.BigIntegerField()
    gmail = models.EmailField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_picture_url = models.TextField(null=True, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    
    # Geographical data
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True)
    
    # Special case: Admin became the initiator
    admin_initiator_id = models.BigIntegerField()  # The admin who voluntarily became initiator
    admin_initiator_name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, default='online')
    is_online = models.BooleanField(default=False)
    
    # NoInitiatorUser specific data (before admin intervention)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    original_verification_status = models.CharField(max_length=20)  # Status before admin took over
    claimed_by_id = models.BigIntegerField(null=True, blank=True)
    claimed_by_name = models.CharField(max_length=255, null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Verification result data
    generated_petitioner_id = models.BigIntegerField()
    generated_usertree_id = models.BigIntegerField()
    verification_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'pendinguser"."no_initiator_verification_history'
        indexes = [
            models.Index(fields=['gmail']),
            models.Index(fields=['verification_date']),
            models.Index(fields=['admin_initiator_id']),
        ]
        verbose_name = "Admin-Initiated No-Initiator Verification"
        verbose_name_plural = "Admin-Initiated No-Initiator Verifications"

    def __str__(self):
        return f"Admin-Initiated: {self.first_name} {self.last_name} by {self.admin_initiator_name}"