from django.db import models, connection
from django.contrib.postgres.fields import ArrayField

class UserTree(models.Model):
    id = models.BigIntegerField(primary_key=True)
    normal_id = models.BigIntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    profilepic = models.ImageField(upload_to='profile_pics/')
    parentid = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    date_of_joining = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    childcount = models.IntegerField(default=0, null=True, blank=True)
    influence = models.IntegerField(default=0, null=True, blank=True)
    height = models.IntegerField(default=0, null=True, blank=True)
    weight = models.IntegerField(default=0, null=True, blank=True)
    depth = models.IntegerField(default=0, null=True, blank=True)

    # Count Fields (from InitiationNuance)
    initiate_count = models.IntegerField(default=0, null=True, blank=True)
    members_count = models.IntegerField(default=0, null=True, blank=True)
    group_members_count = models.IntegerField(default=0, null=True, blank=True)
    
    audience_count = models.IntegerField(default=0, null=True, blank=True)
    shared_audience_count = models.IntegerField(default=0, null=True, blank=True)
    
    connection_count = models.IntegerField(default=0, null=True, blank=True) # ====

    # speakers = ArrayField(
    #     models.IntegerField(), 
    #     blank=True, 
    #     null=True
    # )  # Stores an array of integer IDs within the event row
    # Event-related fields (instead of initiator/speaker/agent)
    EVENT_CHOICES = [
        ('no_event', 'No Event'),
        ('group', 'Group Event'),
        ('public', 'Public Event'),
        ('private', 'Private Event'),
    ]
    event_choice = models.CharField(max_length=20, choices=EVENT_CHOICES, default='no_event')
    event_id = models.BigIntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.update_parent_childcount()
            self.update_grandparent_influence()
            if self.parentid:  # Only create circle relations if parent exists
                self.create_initiator_circle_relation()

    def update_parent_childcount(self):
        """Manually increment the parent's childcount field when adding a child."""
        if self.parentid:
            self.parentid.childcount += 1
            self.parentid.save(update_fields=['childcount'])

    def update_grandparent_influence(self):
        """Update the grandparent's influence count when a new grandchild is added."""
        if self.parentid and self.parentid.parentid:
            grandparent = self.parentid.parentid
            grandparent.influence += 1
            grandparent.save(update_fields=['influence'])
            if hasattr(grandparent, 'check_grandchild_milestone'):
                grandparent.check_grandchild_milestone(getattr(self, 'date_of_joining', None))
    def create_initiator_circle_relation(self):
    
    
        from .Circle import Circle  # Local import to avoid circular dependency

        Circle.objects.create(
            userid=self.id,
            onlinerelation='initiator', 
            otherperson=self.parentid.id
        )
        Circle.objects.create(
            userid=self.parentid.id,
            onlinerelation='initiate',
            otherperson=self.id
        )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'userschema"."usertree'  # Schema-aware table name

