# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import NoInitiatorUser

@shared_task
def unclaim_expired_users():
    """
    Unclaim users that have been claimed for more than 24 hours
    """
    expiration_time = timezone.now() - timedelta(hours=24)
    expired_claims = NoInitiatorUser.objects.filter(
        verification_status="claimed",
        claimed_at__lte=expiration_time
    )
    
    for claim in expired_claims:
        claim.verification_status = "unclaimed"
        claim.claimed_by = None
        claim.claimed_at = None
        claim.save()
    
    return f"Unclaimed {expired_claims.count()} expired claims"