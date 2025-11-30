from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, date
from ..models import UserMonthlyActivity, DailyActivitySummary
from users.models import Petitioner, AdditionalInfo
from .serializers import UserStreakStatusSerializer, MarkActiveSerializer, ActivityHistorySerializer
from django.db import transaction
from users.login.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

class CheckActivityView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    MAX_STREAK_DAYS = 10  # Limit for streak calculation
    
    def get(self, request):
        user_id = request.user.id
        date_str = request.query_params.get('date')

        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse date or default to today
        if date_str:
            try:
                today = date.fromisoformat(date_str)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.localdate()

        yesterday = today - timedelta(days=1)
        start_date = today - timedelta(days=self.MAX_STREAK_DAYS)

        try:
            user = Petitioner.objects.get(id=user_id)
            # Get or create AdditionalInfo if it doesn't exist
            additional_info, created = AdditionalInfo.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'active_days': 0,
                    'last_activity_date': None
                }
            )
            if created:
                logger.info(f"Created AdditionalInfo for user {user_id}")
                
        except Petitioner.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Build date range
        date_range = [today - timedelta(days=i) for i in range(self.MAX_STREAK_DAYS + 1)]

        # Identify relevant months
        months_set = {(d.year, d.month) for d in date_range}

        # Build query
        queries = Q()
        for year, month in months_set:
            queries |= Q(year=year, month=month)

        monthly_activities = UserMonthlyActivity.objects.filter(user=user).filter(queries)

        # Lookup dictionary
        activity_dict = {
            (activity.year, activity.month): set(activity.active_days)
            for activity in monthly_activities
        }

        # Activity checker
        def is_active(target_date):
            key = (target_date.year, target_date.month)
            return key in activity_dict and target_date.day in activity_dict[key]

        is_active_today = is_active(today)
        was_active_yesterday = is_active(yesterday)

        # Streak logic
        streak_count = 0
        if is_active_today:
            streak_count = 1
            current_date = yesterday
            while streak_count < self.MAX_STREAK_DAYS and current_date >= start_date:
                if is_active(current_date):
                    streak_count += 1
                    current_date -= timedelta(days=1)
                else:
                    break

        serializer = UserStreakStatusSerializer(data={
            'is_active_today': is_active_today,
            'was_active_yesterday': was_active_yesterday,
            'streak_count': streak_count,
            'today': today,
            'total_active_days': additional_info.active_days
        })
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ActivityHistoryView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    HISTORY_DAYS = 30  # Last 30 days of activity

    def get(self, request):
        user_id = request.user.id
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = Petitioner.objects.get(id=user_id)
            # Get or create AdditionalInfo
            AdditionalInfo.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'active_days': 0,
                    'last_activity_date': None
                }
            )
        except Petitioner.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

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
                    continue  # Skip invalid dates
        
        # Build history data
        history_data = []
        current_date = start_date
        while current_date <= end_date:
            history_data.append({
                'date': current_date,
                'active': current_date in active_dates
            })
            current_date += timedelta(days=1)
        
        # Return as object with history property
        return Response({'history': history_data})
    

class MarkActiveView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = MarkActiveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = request.user.id
        date_obj = serializer.validated_data['date']
        
        try:
            user = Petitioner.objects.get(id=user_id)
            # Get or create AdditionalInfo if it doesn't exist
            additional_info, created = AdditionalInfo.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'active_days': 0,
                    'last_activity_date': None
                }
            )
            if created:
                logger.info(f"Created AdditionalInfo for user {user_id} during mark-active")
                
        except Petitioner.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            # Update monthly activity
            monthly, created = UserMonthlyActivity.objects.get_or_create(
                user=user,
                year=date_obj.year,
                month=date_obj.month,
                defaults={'active_days': [date_obj.day]}
            )
            
            if not created and date_obj.day not in monthly.active_days:
                monthly.active_days.append(date_obj.day)
                monthly.save()
            
            # Update daily summary
            daily, created = DailyActivitySummary.objects.get_or_create(
                date=date_obj,
                defaults={'active_users': [user.id]}
            )
            
            if not created and user.id not in daily.active_users:
                daily.active_users.append(user.id)
                daily.save()
            
            # Update AdditionalInfo active days and check milestones
            was_updated = additional_info.update_active_days(date_obj)
            
            if was_updated:
                logger.info(f"Successfully updated active days for user {user_id} to {additional_info.active_days}")
            else:
                logger.info(f"User {user_id} was already active on {date_obj}")
        
        return Response(
            {
                'status': 'User marked active successfully',
                'total_active_days': additional_info.active_days,
                'was_updated': was_updated
            },
            status=status.HTTP_200_OK
        )