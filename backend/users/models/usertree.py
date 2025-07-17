from django.db import models
from django.db.models import Max
import logging

logger = logging.getLogger(__name__)

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

    # Count Fields
    initiate_count = models.IntegerField(default=0, null=True, blank=True)
    members_count = models.IntegerField(default=0, null=True, blank=True)
    group_members_count = models.IntegerField(default=0, null=True, blank=True)
    audience_count = models.IntegerField(default=0, null=True, blank=True)
    shared_audience_count = models.IntegerField(default=0, null=True, blank=True)
    connection_count = models.IntegerField(default=0, null=True, blank=True)

    # Event-related fields
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
        
        # Calculate height for new nodes
        if is_new:
            if self.parentid:
                self.height = self.parentid.height + 1
            else:
                self.height = 0
            self.depth = 0  # New nodes start as leaves (depth=0)

        # First save (creates or updates the node)
        super().save(*args, **kwargs)
        
        if is_new:
            self.update_parent_childcount()
            self.update_grandparent_influence()
            if self.parentid:
                self.create_initiator_circle_relation()
            
            # Update ancestor depths
            current = self.parentid
            while current is not None:
                # Get max depth of all children for current ancestor
                max_child_depth = UserTree.objects.filter(
                    parentid=current
                ).aggregate(max_depth=Max('depth'))['max_depth'] or -1
                
                # Calculate new depth: max child depth + 1
                new_depth = max_child_depth + 1
                
                # Only update if depth increases
                if new_depth > current.depth:
                    current.depth = new_depth
                    # Save ONLY the depth field to prevent recursion
                    current.save(update_fields=['depth'])
                    # Move to next ancestor
                    current = current.parentid
                else:
                    # Stop propagation if depth doesn't change
                    break

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
        from event.models.groups import Group  # Local import for group handling

        if self.event_choice == 'private' and self.event_id:
            # User-to-parent relationships
            Circle.objects.create(
                userid=self.id,
                onlinerelation='agent',
                otherperson=self.parentid.id
            )
            Circle.objects.create(
                userid=self.parentid.id,
                onlinerelation='members',
                otherperson=self.id
            )
            
            # Event-linked relationships
            Circle.objects.create(
                userid=self.id,
                onlinerelation='speaker',
                otherperson=self.event_id
            )
            Circle.objects.create(
                userid=self.event_id,
                onlinerelation='audience',
                otherperson=self.id
            )
        elif self.event_choice == 'group' and self.event_id:
            # 1. Create base group relationships with inviter
            Circle.objects.create(
                userid=self.id,
                onlinerelation='groupagent',
                otherperson=self.parentid.id
            )
            Circle.objects.create(
                userid=self.parentid.id,
                onlinerelation='groupmembers',
                otherperson=self.id
            )
            
            try:
                group = Group.objects.get(id=self.event_id)
                
                # 2. Handle speaker relationships based on group configuration
                if group.speakers is None:
                    # Case: No speakers defined - create single speaker relationship with founder
                    if group.founder and group.founder != self.parentid.id:
                        Circle.objects.create(
                            userid=self.id,
                            onlinerelation='speaker',
                            otherperson=group.founder
                        )
                        Circle.objects.create(
                            userid=group.founder,
                            onlinerelation='audience',
                            otherperson=self.id
                        )
                else:
                    # Case: Speakers defined - combine with founder and create multiple speaker relationships
                    speaker_ids = list(set(group.speakers + [group.founder]))
                    
                    for speaker_id in speaker_ids:
                        # Skip creating duplicate for parentid
                        if speaker_id == self.parentid.id:
                            continue
                            
                        Circle.objects.create(
                            userid=self.id,
                            onlinerelation='multiplespeakers',
                            otherperson=speaker_id
                        )
                        Circle.objects.create(
                            userid=speaker_id,
                            onlinerelation='shared_audience',
                            otherperson=self.id
                        )
                
                # 3. Update group membership using Python-side update
                if self.id not in group.members:
                    group.members.append(self.id)
                    group.save(update_fields=['members'])
                    
            except Group.DoesNotExist:
                logger.error(f"Group with ID {self.event_id} not found")
        else:
            # Original behavior for non-private events
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
        db_table = 'userschema"."usertree'

# from django.db import models, connection
# from django.contrib.postgres.fields import ArrayField
# from django.db.models import Max  # Import Max for aggregation

# class UserTree(models.Model):

#     id = models.BigIntegerField(primary_key=True)
#     normal_id = models.BigIntegerField(unique=True, blank=True, null=True)
#     name = models.CharField(max_length=255)
#     profilepic = models.ImageField(upload_to='profile_pics/')
#     parentid = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
#     date_of_joining = models.DateTimeField(auto_now_add=True, null=True, blank=True)

#     childcount = models.IntegerField(default=0, null=True, blank=True)
#     influence = models.IntegerField(default=0, null=True, blank=True)
#     height = models.IntegerField(default=0, null=True, blank=True)
#     weight = models.IntegerField(default=0, null=True, blank=True)
#     depth = models.IntegerField(default=0, null=True, blank=True)

#     # Count Fields (from InitiationNuance)
#     initiate_count = models.IntegerField(default=0, null=True, blank=True)
#     members_count = models.IntegerField(default=0, null=True, blank=True)
#     group_members_count = models.IntegerField(default=0, null=True, blank=True)
    
#     audience_count = models.IntegerField(default=0, null=True, blank=True)
#     shared_audience_count = models.IntegerField(default=0, null=True, blank=True)
    
#     connection_count = models.IntegerField(default=0, null=True, blank=True) # ====

#     # speakers = ArrayField(
#     #     models.IntegerField(), 
#     #     blank=True, 
#     #     null=True
#     # )  # Stores an array of integer IDs within the event row
#     # Event-related fields (instead of initiator/speaker/agent)
#     EVENT_CHOICES = [
#         ('no_event', 'No Event'),
#         ('group', 'Group Event'),
#         ('public', 'Public Event'),
#         ('private', 'Private Event'),
#     ]
#     event_choice = models.CharField(max_length=20, choices=EVENT_CHOICES, default='no_event')
#     event_id = models.BigIntegerField(null=True, blank=True)
    
#     def save(self, *args, **kwargs):
#         is_new = self._state.adding
        
#         # Calculate height for new nodes
#         if is_new:
#             if self.parentid:
#                 self.height = self.parentid.height + 1
#             else:
#                 self.height = 0
#             self.depth = 0  # New nodes start as leaves (depth=0)

#         # First save (creates or updates the node)
#         super().save(*args, **kwargs)
        
#         if is_new:
#             self.update_parent_childcount()
#             self.update_grandparent_influence()
#             if self.parentid:
#                 self.create_initiator_circle_relation()
            
#             # Update ancestor depths
#             current = self.parentid
#             while current is not None:
#                 # Get max depth of all children for current ancestor
#                 max_child_depth = UserTree.objects.filter(
#                     parentid=current
#                 ).aggregate(max_depth=Max('depth'))['max_depth'] or -1
                
#                 # Calculate new depth: max child depth + 1
#                 new_depth = max_child_depth + 1
                
#                 # Only update if depth increases
#                 if new_depth > current.depth:
#                     current.depth = new_depth
#                     # Save ONLY the depth field to prevent recursion
#                     current.save(update_fields=['depth'])
#                     # Move to next ancestor
#                     current = current.parentid
#                 else:
#                     # Stop propagation if depth doesn't change
#                     break

#     def update_parent_childcount(self):
#         """Manually increment the parent's childcount field when adding a child."""
#         if self.parentid:
#             self.parentid.childcount += 1
#             self.parentid.save(update_fields=['childcount'])

#     def update_grandparent_influence(self):
#         """Update the grandparent's influence count when a new grandchild is added."""
#         if self.parentid and self.parentid.parentid:
#             grandparent = self.parentid.parentid
#             grandparent.influence += 1
#             grandparent.save(update_fields=['influence'])
#             if hasattr(grandparent, 'check_grandchild_milestone'):
#                 grandparent.check_grandchild_milestone(getattr(self, 'date_of_joining', None))

    
#     def create_initiator_circle_relation(self):
#         from .Circle import Circle  # Local import to avoid circular dependency
#         from event.models.groups import Group  # Local import for group handling

#         if self.event_choice == 'private' and self.event_id:
#             # User-to-parent relationships (replaces initiator/initiates)
#             Circle.objects.create(
#                 userid=self.id,
#                 onlinerelation='agent',
#                 otherperson=self.parentid.id
#             )
#             Circle.objects.create(
#                 userid=self.parentid.id,
#                 onlinerelation='members',
#                 otherperson=self.id
#             )
            
#             # Event-linked relationships
#             Circle.objects.create(
#                 userid=self.id,
#                 onlinerelation='speaker',
#                 otherperson=self.event_id
#             )
#             Circle.objects.create(
#                 userid=self.event_id,
#                 onlinerelation='audience',
#                 otherperson=self.id
#             )
#         elif self.event_choice == 'group' and self.event_id:
#             # 1. Create base group relationships with inviter
#             Circle.objects.create(
#                 userid=self.id,
#                 onlinerelation='groupmembers',
#                 otherperson=self.parentid.id
#             )
#             Circle.objects.create(
#                 userid=self.parentid.id,
#                 onlinerelation='groupagent',
#                 otherperson=self.id
#             )
            
#             try:
#                 group = Group.objects.get(id=self.event_id)
                
#                 # 2. Handle speaker relationships based on group configuration
#                 if group.speakers is None:
#                     # Case: No speakers defined - create single speaker relationship with founder
#                     if group.founder and group.founder != self.parentid.id:
#                         Circle.objects.create(
#                             userid=self.id,
#                             onlinerelation='audience',
#                             otherperson=group.founder
#                         )
#                         Circle.objects.create(
#                             userid=group.founder,
#                             onlinerelation='speaker',
#                             otherperson=self.id
#                         )
#                 else:
#                     # Case: Speakers defined - combine with founder and create multiple speaker relationships
#                     speaker_ids = list(set(group.speakers + [group.founder]))
                    
#                     for speaker_id in speaker_ids:
#                         # Skip creating duplicate for parentid
#                         if speaker_id == self.parentid.id:
#                             continue
                            
#                         Circle.objects.create(
#                             userid=self.id,
#                             onlinerelation='multiplespeakers',
#                             otherperson=speaker_id
#                         )
#                         Circle.objects.create(
#                             userid=speaker_id,
#                             onlinerelation='shared_audience',
#                             otherperson=self.id
#                         )
                
#                 # 3. Update group membership
#                 if self.id not in group.members:
#                     # Use atomic update to avoid race conditions
#                     Group.objects.filter(id=group.id).update(
#                         members=models.F('members') + [self.id]
#                     )
                
                
                    
#             except Group.DoesNotExist:
#                 pass
#         else:
#             # Original behavior for non-private events
#             Circle.objects.create(
#                 userid=self.id,
#                 onlinerelation='initiator', 
#                 otherperson=self.parentid.id
#             )
#             Circle.objects.create(
#                 userid=self.parentid.id,
#                 onlinerelation='initiate',
#                 otherperson=self.id
#             )

#     def __str__(self):
#         return self.name

#     class Meta:
#         db_table = 'userschema"."usertree'  # Schema-aware table name

