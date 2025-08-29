# models.py
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

class ContributionConflict(models.Model):
    CONFLICT_TYPES = [
        ('ownership', 'Ownership Dispute - I am the true owner'),
        ('collaboration', 'Collaboration - I have done the main part of the work'),
       
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contribution = models.ForeignKey('Contribution', on_delete=models.CASCADE, related_name='conflicts')
    reported_by = models.BigIntegerField()  # User ID of the person reporting the conflict
    conflict_type = models.CharField(max_length=20, choices=CONFLICT_TYPES)
    explanation = models.TextField()
    evidence_urls = ArrayField(
        models.URLField(max_length=400),
        default=list,
        blank=True
    )
    # New fields to store disputed data
    disputed_title = models.CharField(max_length=400, null=True, blank=True)
    disputed_description = models.TextField(null=True, blank=True)
    disputed_teammembers = ArrayField(
        models.BigIntegerField(),
        default=list,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    resolved_by = models.BigIntegerField(null=True, blank=True)  # Admin user ID who resolved it
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blog_related"."contribution_conflict'
        ordering = ['-created_at']

    def __str__(self):
        return f"Conflict for {self.contribution.link} reported by {self.reported_by}"