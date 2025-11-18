from django.core.management.base import BaseCommand
from django.db.models import Count
from event.models import Group
from users.models.usertree import UserTree

class Command(BaseCommand):
    help = 'List all groups with their IDs and basic information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed group information',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Show specific group by ID',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        group_id = options['id']

        if group_id:
            groups = Group.objects.filter(id=group_id)
            if not groups.exists():
                self.stdout.write(
                    self.style.ERROR(f'Group with ID {group_id} not found')
                )
                return
        else:
            groups = Group.objects.all().order_by('id')

        if not groups.exists():
            self.stdout.write(self.style.WARNING('No groups found in database'))
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {groups.count()} group(s) in database:\n')
        )

        for group in groups:
            self.print_group_info(group, detailed)

    def print_group_info(self, group, detailed=False):
        """Print group information in a formatted way"""
        
        # Get founder name if possible
        founder_name = "Unknown"
        try:
            founder = UserTree.objects.filter(id=group.founder).first()
            if founder:
                founder_name = founder.name
        except:
            pass

        self.stdout.write(
            self.style.SUCCESS(f'┌─ Group ID: {group.id}')
        )
        self.stdout.write(f'│  Name: {group.name}')
        self.stdout.write(f'│  Founder: {founder_name} (ID: {group.founder})')
        self.stdout.write(f'│  Created: {group.created_at.strftime("%Y-%m-%d %H:%M")}')
        
        if detailed:
            self.stdout.write(f'│  Speakers: {len(group.speakers)} users')
            self.stdout.write(f'│  Members: {len(group.members)} users')
            self.stdout.write(f'│  Pending Speakers: {len(group.pending_speakers)} users')
            self.stdout.write(f'│  Institution: {group.institution or "Not set"}')
            
            # Location info
            location_parts = []
            if group.village: location_parts.append(str(group.village))
            if group.subdistrict: location_parts.append(str(group.subdistrict))
            if group.district: location_parts.append(str(group.district))
            if group.state: location_parts.append(str(group.state))
            if group.country: location_parts.append(str(group.country))
            
            location = ', '.join(location_parts) if location_parts else "Not set"
            self.stdout.write(f'│  Location: {location}')
            
            # Show actual speaker IDs if any
            if group.speakers:
                self.stdout.write(f'│  Speaker IDs: {group.speakers}')
            
            # Show member IDs if any
            if group.members:
                self.stdout.write(f'│  Member IDs: {group.members}')

        self.stdout.write('└' + '─' * 50)

    def print_summary(self, groups):
        """Print a summary of groups"""
        total_speakers = sum(len(group.speakers) for group in groups)
        total_members = sum(len(group.members) for group in groups)
        total_pending = sum(len(group.pending_speakers) for group in groups)
        
        self.stdout.write(
            self.style.SUCCESS('\n📊 GROUP SUMMARY:')
        )
        self.stdout.write(f'• Total Groups: {groups.count()}')
        self.stdout.write(f'• Total Speakers: {total_speakers}')
        self.stdout.write(f'• Total Members: {total_members}')
        self.stdout.write(f'• Total Pending Speakers: {total_pending}')
        
        # Groups with no members (setup not completed)
        groups_without_members = [g for g in groups if not g.members]
        self.stdout.write(
            self.style.WARNING(f'• Groups needing setup: {len(groups_without_members)}')
        )