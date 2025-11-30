from django.db.models import Q
from datetime import date, timedelta
from users.models import Petitioner, UserTree
from ..models import UserMonthlyActivity
from users.models import Circle
from users.profilepic_manager.utils import get_profilepic_url
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import models
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

class HeartbeatNetworkView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    HISTORY_DAYS = 30

    def get(self, request):
        logger.info("=== HEARTBEAT NETWORK VIEW STARTED ===")
        
        user_id = request.user.id
        logger.info(f"User ID from request: {user_id}")
        
        if not user_id:
            logger.error("No user_id found in request")
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Petitioner.objects.get(id=user_id)
            logger.info(f"Found user: {user.first_name} {user.last_name}")
        except Petitioner.DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.localdate()
        logger.info(f"Today's date: {today}")

        # Get current state from request parameters
        current_active_ids = request.GET.get('active_ids', '')
        current_inactive_ids = request.GET.get('inactive_ids', '')
        
        # If no parameters provided, it's first load - send full data
        if not current_active_ids and not current_inactive_ids:
            logger.info("First load - sending full network data")
            network_data = self.build_network_data(user_id, today, request)
            return Response({
                'network_users': network_data,
                'current_user_id': user_id,
                'today': today.isoformat(),
                'update_type': 'full'
            })
        
        # Subsequent loads - check for updates
        active_ids_set = set(int(id) for id in current_active_ids.split(',')) if current_active_ids else set()
        inactive_ids_set = set(int(id) for id in current_inactive_ids.split(',')) if current_inactive_ids else set()
        
        logger.info(f"Client sent - Active: {len(active_ids_set)}, Inactive: {len(inactive_ids_set)}")

        # Check for updates
        needs_full_refresh, activity_updates = self.check_for_updates(
            user_id, today, active_ids_set, inactive_ids_set
        )

        if needs_full_refresh:
            logger.info("New users detected - sending full refresh")
            network_data = self.build_network_data(user_id, today, request)
            return Response({
                'network_users': network_data,
                'current_user_id': user_id,
                'today': today.isoformat(),
                'update_type': 'full'
            })
        elif activity_updates:
            logger.info(f"Sending activity updates for {len(activity_updates)} users")
            return Response({
                'network_users': [],
                'current_user_id': user_id,
                'today': today.isoformat(),
                'update_type': 'activity_updates',
                'activity_updates': activity_updates
            })
        else:
            logger.info("No changes detected")
            return Response({
                'network_users': [],
                'current_user_id': user_id,
                'today': today.isoformat(),
                'update_type': 'no_changes'
            })

    def check_for_updates(self, user_id, today, client_active_ids, client_inactive_ids):
        """Check if there are any updates needed"""
        logger.info("Checking for updates...")
        
        # Get current connections from database
        current_connections = self.get_current_connections(user_id)
        current_connection_ids = set(current_connections.keys())
        
        # Check if client has all current connections
        client_all_ids = client_active_ids.union(client_inactive_ids)
        new_users = current_connection_ids - client_all_ids
        
        if new_users:
            logger.info(f"New users detected: {len(new_users)}")
            return True, []
        
        # Check for activity status changes
        activity_updates = self.check_activity_changes(
            client_active_ids, client_inactive_ids, today
        )
        
        return False, activity_updates

    def get_current_connections(self, user_id):
        """Get current connections with their relationship types"""
        connections = Circle.objects.filter(
            Q(userid=user_id) | Q(otherperson=user_id)
        ).distinct()
        
        connection_dict = {}
        
        for connection in connections:
            if connection.userid == user_id:
                connection_user_id = connection.otherperson
                connection_type = connection.onlinerelation
            else:
                connection_user_id = connection.userid
                connection_type = self.get_reverse_relation(connection.onlinerelation)

            if connection_user_id and connection_user_id != user_id:
                connection_dict[connection_user_id] = connection_type
        
        logger.info(f"Found {len(connection_dict)} current connections")
        return connection_dict

    def check_activity_changes(self, client_active_ids, client_inactive_ids, today):
        """Check if any users' activity status has changed"""
        all_user_ids = client_active_ids.union(client_inactive_ids)
        
        if not all_user_ids:
            return []
        
        # Get current activity status for all users
        current_activity_status = self.get_bulk_activity_status(all_user_ids, today)
        
        activity_updates = []
        
        for user_id in all_user_ids:
            current_status = current_activity_status.get(user_id, {'is_active_today': False, 'streak_count': 0})
            was_active = user_id in client_active_ids
            
            if current_status['is_active_today'] != was_active:
                activity_updates.append({
                    'user_id': user_id,
                    'is_active_today': current_status['is_active_today'],
                    'streak_count': current_status['streak_count']
                })
                logger.info(f"Activity change for user {user_id}: {was_active} -> {current_status['is_active_today']}")
        
        return activity_updates

    def build_network_data(self, user_id, today, request):
        """Build complete network data"""
        logger.info("Building complete network data")
        
        connections = Circle.objects.filter(
            Q(userid=user_id) | Q(otherperson=user_id)
        ).distinct()
        
        logger.info(f"Found {connections.count()} total connections")

        network_data = []
        processed_user_ids = set()
        connection_user_ids = set()
        
        # Collect connection user IDs
        for connection in connections:
            if connection.userid != user_id:
                connection_user_ids.add(connection.userid)
            if connection.otherperson != user_id:
                connection_user_ids.add(connection.otherperson)
        
        logger.info(f"Collected {len(connection_user_ids)} unique connection user IDs")
        
        # Bulk fetch data
        petitioners_dict = {
            p.id: p for p in Petitioner.objects.filter(id__in=connection_user_ids)
        }
        user_trees_dict = {
            ut.id: ut for ut in UserTree.objects.filter(id__in=connection_user_ids)
        }
        
        # Bulk activity status
        bulk_activity_status = self.get_bulk_activity_status(connection_user_ids, today)
        
        for connection in connections:
            if connection.userid == user_id:
                connection_user_id = connection.otherperson
                connection_type = connection.onlinerelation
            else:
                connection_user_id = connection.userid
                connection_type = self.get_reverse_relation(connection.onlinerelation)

            if not connection_user_id or connection_user_id == user_id or connection_user_id in processed_user_ids:
                continue

            try:
                connection_user = petitioners_dict.get(connection_user_id)
                user_tree = user_trees_dict.get(connection_user_id)
                
                if not connection_user or not user_tree:
                    logger.warning(f"Missing data for user {connection_user_id}")
                    continue
                
                activity_status = bulk_activity_status.get(connection_user_id, {'is_active_today': False, 'streak_count': 0})
                activity_history = self.get_user_activity_history(connection_user_id)
                profile_pic = get_profilepic_url(user_tree, request)
                
                network_data.append({
                    'id': connection_user_id,
                    'name': f"{connection_user.first_name} {connection_user.last_name}",
                    'profile_pic': profile_pic,
                    'connection_type': connection_type,
                    'is_active_today': activity_status['is_active_today'],
                    'streak_count': activity_status['streak_count'],
                    'activity_history': activity_history
                })
                
                processed_user_ids.add(connection_user_id)
                
            except Exception as e:
                logger.error(f"Error processing connection for user {connection_user_id}: {str(e)}")
                continue

        logger.info(f"Built network data with {len(network_data)} users")
        return network_data

    def get_bulk_activity_status(self, user_ids, target_date):
        """Get activity status for multiple users in bulk"""
        if not user_ids:
            return {}
        
        yesterday = target_date - timedelta(days=1)
        start_date = target_date - timedelta(days=10)

        # Get relevant months for activity check
        months_set = {
            (target_date.year, target_date.month),
            (yesterday.year, yesterday.month)
        }
        for i in range(10):
            check_date = target_date - timedelta(days=i)
            months_set.add((check_date.year, check_date.month))

        # Build query for monthly activities
        queries = Q()
        for year, month in months_set:
            queries |= Q(year=year, month=month)
        
        monthly_activities = UserMonthlyActivity.objects.filter(
            user_id__in=user_ids
        ).filter(queries)
        
        # Organize activities by user
        user_activities = {}
        for activity in monthly_activities:
            if activity.user_id not in user_activities:
                user_activities[activity.user_id] = []
            user_activities[activity.user_id].append(activity)
        
        # Calculate status for each user
        result = {}
        for user_id in user_ids:
            activities = user_activities.get(user_id, [])
            activity_dict = {
                (activity.year, activity.month): set(activity.active_days)
                for activity in activities
            }
            
            def is_active(check_date):
                key = (check_date.year, check_date.month)
                return key in activity_dict and check_date.day in activity_dict[key]
            
            is_active_today = is_active(target_date)
            streak_count = 0
            
            if is_active_today:
                streak_count = 1
                current_date = yesterday
                while streak_count < 10 and current_date >= start_date:
                    if is_active(current_date):
                        streak_count += 1
                        current_date -= timedelta(days=1)
                    else:
                        break
            
            result[user_id] = {
                'is_active_today': is_active_today,
                'streak_count': streak_count
            }
        
        return result

    def get_reverse_relation(self, relation):
        """Get the reverse relationship type"""
        reverse_map = {
            'initiate': 'initiator',
            'initiator': 'initiate',
            'online_initiate': 'online_initiator',
            'online_initiator': 'online_initiate',
            'agent': 'members',
            'members': 'agent',
            'speaker': 'audience',
            'audience': 'speaker',
            'groupagent': 'groupmembers',
            'groupmembers': 'groupagent',
            'multiplespeakers': 'shared_audience',
            'shared_audience': 'multiplespeakers'
        }
        return reverse_map.get(relation, relation)

    def get_user_activity_history(self, user_id):
        """Get activity history for a user (last 30 days)"""
        try:
            user = Petitioner.objects.get(id=user_id)
        except Petitioner.DoesNotExist:
            return []

        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=self.HISTORY_DAYS - 1)
        
        # Get all months in the date range
        months_set = set()
        current_date = start_date
        while current_date <= end_date:
            months_set.add((current_date.year, current_date.month))
            current_date += timedelta(days=1)
        
        # Build query for these months
        queries = Q()
        for year, month in months_set:
            queries |= Q(year=year, month=month)
        
        monthly_activities = UserMonthlyActivity.objects.filter(user=user).filter(queries)
        
        # Create a dictionary of active dates
        active_dates = set()
        for activity in monthly_activities:
            for day in activity.active_days:
                try:
                    active_date = date(activity.year, activity.month, day)
                    if start_date <= active_date <= end_date:
                        active_dates.add(active_date)
                except ValueError:
                    continue
        
        # Build history data
        history_data = []
        current_date = start_date
        while current_date <= end_date:
            history_data.append({
                'date': current_date.isoformat(),
                'active': current_date in active_dates
            })
            current_date += timedelta(days=1)
        
        return history_data