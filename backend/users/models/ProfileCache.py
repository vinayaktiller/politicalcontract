# models.py - Add this to your users models or create a new models file
from django.db import models
from django.utils import timezone

class ProfileCache(models.Model):
    user = models.OneToOneField('users.Petitioner', on_delete=models.CASCADE, primary_key=True)
    profile_data = models.JSONField()  # Stores all the serialized profile data
    generated_at = models.DateTimeField(auto_now=True)
    last_activity_check = models.DateTimeField()  # When we last checked for activity changes
    is_stale = models.BooleanField(default=False)  # Flag to force regeneration
    
    class Meta:
        db_table = 'userschema"."profile_cache'
        verbose_name_plural = 'Profile Caches'
    
    def __str__(self):
        return f"Profile cache for {self.user.first_name}"
    
    def is_expired(self):
        """Check if cache is older than 1 day"""
        return (timezone.now() - self.generated_at).days >= 1
    
    def needs_regeneration(self):
        """Check if cache needs to be regenerated"""
        return self.is_stale or self.is_expired()