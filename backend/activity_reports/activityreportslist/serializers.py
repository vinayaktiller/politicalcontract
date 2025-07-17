from rest_framework import serializers
from ..models import (
    DailyCountryActivityReport,
    WeeklyCountryActivityReport,
    MonthlyCountryActivityReport
)

class CountryActivityReportSerializer(serializers.Serializer):
    report_type = serializers.SerializerMethodField()
    id = serializers.IntegerField()
    formatted_date = serializers.SerializerMethodField()
    active_users = serializers.IntegerField()
    country_id = serializers.IntegerField(source='country.id')
    country_name = serializers.CharField(source='country.name')

    def get_report_type(self, obj):
        if isinstance(obj, DailyCountryActivityReport):
            return 'daily'
        elif isinstance(obj, WeeklyCountryActivityReport):
            return 'weekly'
        elif isinstance(obj, MonthlyCountryActivityReport):
            return 'monthly'
    
    def get_formatted_date(self, obj):
        if isinstance(obj, DailyCountryActivityReport):
            return obj.date.strftime("%d %b %Y")
        elif isinstance(obj, WeeklyCountryActivityReport):
            return f"{obj.week_start_date.strftime('%d %b')} – {obj.week_last_date.strftime('%d %b %Y')}"
        elif isinstance(obj, MonthlyCountryActivityReport):
            return obj.last_date.strftime("%B %Y")