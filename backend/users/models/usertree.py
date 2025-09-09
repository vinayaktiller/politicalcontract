from django.db import models
from django.db.models import Max
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class UserTree(models.Model):
    # Milestone definitions as class-level constants
    INITIATION_MILESTONES = {
        1: ("Worker", "you are a worker, you have initiated 1 member."),
        5: ("Initiator", "With 5 members initiated, you solidify your place as a key initiator and a community builder."),
        10: ("Promoter", "Initiating 10 members demonstrates your ability to promote community expansion and foster engagement."),
        20: ("Seeder", "Initiating 20 members shows you’re seeding the community with potential and laying the foundation for future growth."),
        25: ("Cader", "Reaching 25 initiations signifies that you have become a core pillar of the movement, leading with dedication and vision."),
        30: ("Harbinger", "Achieving 30 initiations, you herald new beginnings and embody a vibrant spirit of growth."),
        40: ("Manson", "At 40 initiations, you reinforce your impact, demonstrating masterful skill in building a resilient community."),
        50: ("Beacon", "Reaching 50 initiations, you shine as a beacon of inspiration, guiding others with your radiant leadership.")
    }

    INFLUENCE_MILESTONES = {
        25: ("Influencer", "Your influence goes beyond your direct actions—your initiates are now bringing others into the movement."),
        50: ("Planter", "Not only do you sow the seeds of initiation, but you also nurture a network that bears fruits of its own."),
        100: ("Harvester", "Your initiates are flourishing, bringing 100 more people into the movement—you now reap the rewards of your leadership."),
        200: ("Teacher", "Your wisdom and guidance have created a ripple effect of knowledge and leadership within the community."),
        400: ("Gardener", "You cultivate a thriving ecosystem where initiates flourish like plants, bearing fruit for generations to come."),
        500: ("Forester", "You have gone beyond a garden—you have built a forest, a self-sustaining ecosystem of influence."),
        625: ("Steward", "As a steward, you protect and nurture the growth of the movement, ensuring its future prosperity."),
        750: ("Catalyst", "Your actions accelerate change, igniting a powerful movement that transforms communities."),
        900: ("Movement", "You are no longer just an initiator; you are the movement itself—leading a historic transformation."),
        1000: ("Torchbearer", "Reaching your influence on 1000 initiations, you light the way for countless others, carrying the torch of leadership and change."),
        1500: ("Symbol", "You have become an icon, a figure of inspiration whose influence shapes the very essence of this community."),
    }

    connexions_milestones = {
        5: ("Tailor", "With 5 connexions, your circle is well-fitted to the movement. You shape solidarity with precision and care."),
        10: ("Binder", "10 connexions show your ties are strong and purposeful. You are bound to a circle that walks the path of change."),
        20: ("Embroiderer", "At 20 connexions, your presence adds intricate detail to a collective tapestry. You are among those who carry the spirit of the movement."),
        30: ("Goldsmith", "With 30 connexions, your circle gleams with legacy and resilience. You are adorned by the strength of those around you."),
        40: ("Potter", "40 connexions reflect a grounded community shaped by shared purpose. You mold and hold space for transformation."),
        50: ("Weaver", "With 50 connexions, your threads are tightly woven into the fabric of the movement. You belong to a community already aligned.")
    }

    # Fields
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
        ('online', 'Online Initiation'),  # Added online initiation type
    ]
    event_choice = models.CharField(max_length=20, choices=EVENT_CHOICES, default='no_event')
    event_id = models.BigIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Calculate height and default depth for new nodes
        if is_new:
            if self.parentid:
                self.height = self.parentid.height + 1
            else:
                self.height = 0
            self.depth = 0  # New nodes start as leaves

        super().save(*args, **kwargs)

        if is_new:
            self.update_parent_childcount()
            self.update_grandparent_influence()
            if self.parentid:
                self.create_initiator_circle_relation()

            # Update ancestor depths up the tree
            current = self.parentid
            while current is not None:
                max_child_depth = UserTree.objects.filter(parentid=current).aggregate(max_depth=Max('depth'))['max_depth'] or -1
                new_depth = max_child_depth + 1
                if new_depth > current.depth:
                    current.depth = new_depth
                    current.save(update_fields=['depth'])
                    current = current.parentid
                else:
                    break

    def update_parent_childcount(self):
        """Increment parent's childcount and check milestone."""
        if self.parentid:
            self.parentid.childcount += 1
            self.parentid.save(update_fields=['childcount'])
            if hasattr(self.parentid, 'check_milestone'):
                self.parentid.check_milestone()

    def update_grandparent_influence(self):
        """Increment grandparent's influence and check milestone."""
        if self.parentid and self.parentid.parentid:
            grandparent = self.parentid.parentid
            grandparent.influence += 1
            grandparent.save(update_fields=['influence'])
            if hasattr(grandparent, 'check_grandchild_milestone'):
                grandparent.check_grandchild_milestone()

    def check_milestone(self):
        """Check and create initiation milestone if any."""
        if self.childcount in self.INITIATION_MILESTONES:
            title, text = self.INITIATION_MILESTONES[self.childcount]
            self.create_milestone(title, text, 'initiation', self.childcount)

    def check_grandchild_milestone(self):
        """Check and create influence milestone if any."""
        if self.influence in self.INFLUENCE_MILESTONES:
            title, text = self.INFLUENCE_MILESTONES[self.influence]
            self.create_milestone(title, text, 'influence', self.influence)

    def create_milestone(self, title, text, milestone_type=None, level=None):
        from .petitioners import Petitioner
        from .milestone import Milestone

        try:
            petitioner = Petitioner.objects.get(id=self.id)
            gender = petitioner.gender
        except Petitioner.DoesNotExist:
            gender = 'M'
            logger.error(f"Petitioner not found for UserTree ID: {self.id}")

        photo_id = None

        if milestone_type == 'initiation' and level is not None:
            levels = sorted(self.INITIATION_MILESTONES.keys())
            milestone_index = levels.index(level)
            gender_offset = 0 if gender == 'M' else 1
            photo_id = milestone_index * 2 + gender_offset + 1
        elif milestone_type == 'influence' and level is not None:
            levels = sorted(self.INFLUENCE_MILESTONES.keys())
            milestone_index = levels.index(level)
            gender_offset = 0 if gender == 'M' else 1
            photo_id = milestone_index * 2 + gender_offset + 1

        if not Milestone.objects.filter(user_id=self.id, title=title).exists():
            Milestone.objects.create(
                user_id=self.id,
                title=title,
                text=text,
                type=milestone_type,
                photo_id=photo_id,
                created_at=timezone.now()
            )

    def create_initiator_circle_relation(self):
        from .Circle import Circle  # Local import to avoid circular dependency
        from event.models.groups import Group  # Local import for group handling

        if self.event_choice == 'online':  # Handle online initiation
            Circle.objects.create(
                userid=self.id,
                onlinerelation='online_initiate',
                otherperson=self.parentid.id
            )
            Circle.objects.create(
                userid=self.parentid.id,
                onlinerelation='online_initiator',
                otherperson=self.id
            )
        elif self.event_choice == 'private' and self.event_id:
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
                if group.speakers is None:
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
                    speaker_ids = list(set(group.speakers + [group.founder]))
                    for speaker_id in speaker_ids:
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
                if self.id not in group.members:
                    group.members.append(self.id)
                    group.save(update_fields=['members'])
            except Group.DoesNotExist:
                logger.error(f"Group with ID {self.event_id} not found")
        else:
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
