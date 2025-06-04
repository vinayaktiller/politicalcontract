import uuid
from django.db import models

class Circle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Using UUID instead of BigAutoField
    userid = models.BigIntegerField(null=True, blank=True) 
    
    ONLINE_RELATION_CHOICES = [
        ('initiator', 'Initiator'),
        ('initiates', 'Initiates'),
        ('agent', 'Agent'),
        ('members', 'Members'),
        ('groupagent', 'Group Agent'),
        ('groupmembers', 'Group Members'),
        ('speaker', 'Speaker'),
        ('audience', 'Audience'),
        ('shared_audience', 'Shared Audience'),
        ('connections', 'Connections'),
        ('speakers', 'Speakers'),
    ]
    
    OFFLINE_RELATION_CHOICES = [
        ('family', 'Family'),
        ('friends', 'Friends'),
        ('colleagues', 'Colleagues'),
        ('relatives', 'Relatives'),
        ('neighbours', 'Neighbours'),
        ('acquaintances', 'Acquaintances'),
        ('classmates', 'Classmates'),
        ('teammates', 'Teammates'),
        ('unknown', 'Unknown'),
        ('others', 'Others'),
    ]

    onlinerelation = models.CharField(max_length=50, choices=ONLINE_RELATION_CHOICES)
    offlinerelation = models.CharField(max_length=50, choices=OFFLINE_RELATION_CHOICES, default='unknown')  # Default to 'unknown' for offline relation
    label = models.CharField(max_length=255, null=True, blank=True)  # Optional label for the circle
    otherperson = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Circle of {self.userid} - {self.label}"

    class Meta:
        db_table = 'userschema"."circle'  # Schema-aware table name
