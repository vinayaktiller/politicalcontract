from rest_framework import serializers
from datetime import date

class UserStreakStatusSerializer(serializers.Serializer):
    is_active_today = serializers.BooleanField()
    was_active_yesterday = serializers.BooleanField()
    streak_count = serializers.IntegerField(min_value=0)
    today = serializers.DateField(default=date.today)

class MarkActiveSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    date = serializers.DateField()

class ActivityHistoryItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    active = serializers.BooleanField()

# In your serializers.py
class ActivityHistorySerializer(serializers.Serializer):
    date = serializers.DateField()
    active = serializers.BooleanField()