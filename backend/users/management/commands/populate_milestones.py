from django.core.management.base import BaseCommand
from django.utils import timezone
from ...models import UserTree, Milestone, Petitioner

import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Populate milestone records retrospectively for existing users in UserTree"

    def handle(self, *args, **options):
        # Fetch all UserTree users
        users = UserTree.objects.all()
        total_users = users.count()
        milestones_created = 0
        
        # Milestone dictionaries (mirroring model class constants)
        initiation_milestones = UserTree.INITIATION_MILESTONES
        influence_milestones = UserTree.INFLUENCE_MILESTONES

        for user in users.iterator():
            try:
                petitioner = Petitioner.objects.get(id=user.id)
                gender = petitioner.gender
            except Petitioner.DoesNotExist:
                logger.warning(f"Petitioner not found for UserTree ID: {user.id}, defaulting gender to 'M'")
                gender = 'M'  # Default if no petitioner

            # Check initiation milestones retroactively
            for level, (title, text) in initiation_milestones.items():
                if user.childcount >= level:
                    # Calculate photo_id similar to model logic
                    levels = sorted(initiation_milestones.keys())
                    milestone_index = levels.index(level)
                    gender_offset = 0 if gender == 'M' else 1
                    photo_id = milestone_index * 2 + gender_offset + 1

                    if not Milestone.objects.filter(user_id=user.id, title=title).exists():
                        Milestone.objects.create(
                            user_id=user.id,
                            title=title,
                            text=text,
                            type='initiation',
                            photo_id=photo_id,
                            created_at=timezone.now(),
                            delivered=True
                        )
                        milestones_created += 1

            # Check influence milestones retroactively
            for level, (title, text) in influence_milestones.items():
                if user.influence >= level:
                    levels = sorted(influence_milestones.keys())
                    milestone_index = levels.index(level)
                    gender_offset = 0 if gender == 'M' else 1
                    # Offset photo IDs for influence milestones after initiation milestones
                    photo_id = milestone_index * 2 + gender_offset + 1

                    if not Milestone.objects.filter(user_id=user.id, title=title).exists():
                        Milestone.objects.create(
                            user_id=user.id,
                            title=title,
                            text=text,
                            type='influence',
                            photo_id=photo_id,
                            created_at=timezone.now(),
                        )
                        milestones_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Milestone retroactive population completed. Total users processed: {total_users}. "
            f"Milestones created: {milestones_created}."
        ))
