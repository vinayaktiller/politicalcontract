# serializers.py
from rest_framework import serializers
from ..models.intitationreports import (
    CountryDailyReport,
    CountryWeeklyReport,
    CountryMonthlyReport
)


class CountryReportSerializer(serializers.Serializer):
    report_type = serializers.SerializerMethodField()
    id = serializers.UUIDField(format='hex_verbose')  # ✅ Changed from IntegerField to UUIDField
    formatted_date = serializers.SerializerMethodField()
    new_users = serializers.IntegerField()
    country_id = serializers.IntegerField(source='country.id')
    country_name = serializers.CharField(source='country.name')

    def get_report_type(self, obj):
        if isinstance(obj, CountryDailyReport):
            return 'daily'
        elif isinstance(obj, CountryWeeklyReport):
            return 'weekly'
        elif isinstance(obj, CountryMonthlyReport):
            return 'monthly'
        return None

    def get_formatted_date(self, obj):
        if isinstance(obj, CountryDailyReport):
            return obj.date.strftime("%d %b %Y")
        elif isinstance(obj, CountryWeeklyReport):
            return f"{obj.week_start_date.strftime('%d %b')} – {obj.week_last_date.strftime('%d %b %Y')}"
        elif isinstance(obj, CountryMonthlyReport):
            return obj.last_date.strftime("%B %Y")
        return None
