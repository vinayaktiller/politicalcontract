import random
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import Petitioner, UserTree, Circle
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates symmetric connections between users in the Circle model'
    
    def add_arguments(self, parser):
        parser.add_argument('--min-connections', type=int, default=5, help='Minimum connections per user')
        parser.add_argument('--max-connections', type=int, default=15, help='Maximum connections per user')
        parser.add_argument('--flush', action='store_true', help='Delete existing Circle data first')
    
    def handle(self, *args, **options):
        min_conn = options['min_connections']
        max_conn = options['max_connections']
        flush = options['flush']
        
        if flush:
            self.stdout.write("Flushing Circle data...")
            Circle.objects.all().delete()
        
        # Get all users and existing connections
        all_users = list(Petitioner.objects.values_list('id', flat=True))
        existing_pairs = self.get_existing_connections()
        
        # Create new connections
        new_connections = self.generate_connections(
            all_users, 
            existing_pairs,
            min_conn,
            max_conn
        )
        
        # Save to database
        self.create_circle_entries(new_connections)
        self.stdout.write(self.style.SUCCESS(
            f"Created {len(new_connections)} bidirectional connections "
            f"({len(new_connections)*2} Circle records)"
        ))
    
    def get_existing_connections(self):
        """Get existing connections from UserTree and Circle"""
        existing_pairs = set()
        
        # Get parent-child relationships from UserTree
        for node in UserTree.objects.exclude(parentid=None):
            a, b = node.id, node.parentid.id
            existing_pairs.add((min(a, b), max(a, b)))
        
        # Get existing Circle relationships
        for circle in Circle.objects.all():
            if circle.userid and circle.otherperson:
                a, b = circle.userid, circle.otherperson
                existing_pairs.add((min(a, b), max(a, b)))
        
        return existing_pairs
    
    def generate_connections(self, users, existing_pairs, min_conn, max_conn):
        """Generate new symmetric connections between users"""
        user_connections = defaultdict(set)
        new_pairs = set()
        
        # Prepare user pool and shuffle
        user_pool = users.copy()
        random.shuffle(user_pool)
        
        for user in user_pool:
            # Determine how many connections this user needs
            current_count = len(user_connections[user])
            needed = max(0, random.randint(min_conn, max_conn) - current_count)
            
            # Find suitable candidates
            candidates = [
                u for u in user_pool 
                if u != user 
                and u not in user_connections[user]
                and (min(user, u), max(user, u)) not in existing_pairs
            ]
            random.shuffle(candidates)
            
            # Create new connections
            for candidate in candidates[:needed]:
                pair = (min(user, candidate), max(user, candidate))
                
                if pair not in existing_pairs and pair not in new_pairs:
                    new_pairs.add(pair)
                    user_connections[user].add(candidate)
                    user_connections[candidate].add(user)
        
        return new_pairs
    
    def create_circle_entries(self, connections):
        """Create Circle entries for each connection pair"""
        online_relations = [
            'connections', 
            'shared_audience',
            'members',
            'groupmembers',
            'multiplespeakers'
        ]
        
        offline_relations = [
            'friends',
            'colleagues',
            'relatives',
            'neighbours',
            'acquaintances',
            'classmates',
            'teammates'
        ]
        
        circle_entries = []
        
        for user1, user2 in connections:
            # Choose random symmetric relations
            online_rel = random.choice(online_relations)
            offline_rel = random.choice(offline_relations)
            label = f"{online_rel} ({offline_rel})"
            
            # Create bidirectional entries
            circle_entries.append(Circle(
                userid=user1,
                otherperson=user2,
                onlinerelation=online_rel,
                offlinerelation=offline_rel,
                label=label
            ))
            
            circle_entries.append(Circle(
                userid=user2,
                otherperson=user1,
                onlinerelation=online_rel,
                offlinerelation=offline_rel,
                label=label
            ))
        
        # Bulk create all entries
        Circle.objects.bulk_create(circle_entries)


# # Create connections (5-15 per user)
# python manage.py create_connections

# # Create more connections (10-20 per user)
# python manage.py create_connections --min-connections=10 --max-connections=20

# # Reset and recreate connections
# python manage.py create_connections --flush