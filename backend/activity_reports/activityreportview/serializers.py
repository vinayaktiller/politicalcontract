# serializers.py
from rest_framework import serializers
from ..models import (
    DailyVillageActivityReport, WeeklyVillageActivityReport, MonthlyVillageActivityReport,
    DailySubdistrictActivityReport, WeeklySubdistrictActivityReport, MonthlySubdistrictActivityReport,
    DailyDistrictActivityReport, WeeklyDistrictActivityReport, MonthlyDistrictActivityReport,
    DailyStateActivityReport, WeeklyStateActivityReport, MonthlyStateActivityReport,
    DailyCountryActivityReport, WeeklyCountryActivityReport, MonthlyCountryActivityReport
)
from geographies.models.geos import Village, Subdistrict, District, State, Country

class BaseActivityReportSerializer(serializers.ModelSerializer):
    geographical_entity = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    parent_info = serializers.SerializerMethodField()
    children_data = serializers.SerializerMethodField()
    additional_info = serializers.SerializerMethodField()

    def get_geographical_entity(self, obj):
        entity = getattr(obj, self.Meta.entity_field)
        return {
            'id': entity.id,
            'name': entity.name,
            'type': self.Meta.entity_type
        }

    def get_level(self, obj):
        return self.Meta.level

    def get_parent_info(self, obj):
        if not hasattr(obj, 'parent_id') or not obj.parent_id:
            return None
        
        parent_level = {
            'village': 'subdistrict',
            'subdistrict': 'district',
            'district': 'state',
            'state': 'country'
        }.get(self.Meta.level)
        
        if not parent_level:
            return None

        return {
            'level': parent_level,
            'report_id': obj.parent_id
        }

    def get_children_data(self, obj):
        return getattr(obj, self.Meta.children_field, {})

    def get_additional_info(self, obj):
        # Only return additional_info if it exists and is not empty
        if hasattr(obj, 'additional_info') and obj.additional_info:
            return obj.additional_info
        return None

    class Meta:
        abstract = True

# Village Serializers
class DailyVillageActivityReportSerializer(BaseActivityReportSerializer):
    class Meta:
        model = DailyVillageActivityReport
        fields = '__all__'
        entity_field = 'village'
        entity_type = 'village'
        level = 'village'
        children_field = 'user_data'

class WeeklyVillageActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyVillageActivityReportSerializer.Meta):
        model = WeeklyVillageActivityReport

class MonthlyVillageActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyVillageActivityReportSerializer.Meta):
        model = MonthlyVillageActivityReport

# Subdistrict Serializers
class DailySubdistrictActivityReportSerializer(BaseActivityReportSerializer):
    class Meta:
        model = DailySubdistrictActivityReport
        fields = '__all__'
        entity_field = 'subdistrict'
        entity_type = 'subdistrict'
        level = 'subdistrict'
        children_field = 'village_data'

class WeeklySubdistrictActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailySubdistrictActivityReportSerializer.Meta):
        model = WeeklySubdistrictActivityReport

class MonthlySubdistrictActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailySubdistrictActivityReportSerializer.Meta):
        model = MonthlySubdistrictActivityReport

# District Serializers
class DailyDistrictActivityReportSerializer(BaseActivityReportSerializer):
    class Meta:
        model = DailyDistrictActivityReport
        fields = '__all__'
        entity_field = 'district'
        entity_type = 'district'
        level = 'district'
        children_field = 'subdistrict_data'

class WeeklyDistrictActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyDistrictActivityReportSerializer.Meta):
        model = WeeklyDistrictActivityReport

class MonthlyDistrictActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyDistrictActivityReportSerializer.Meta):
        model = MonthlyDistrictActivityReport

# State Serializers
class DailyStateActivityReportSerializer(BaseActivityReportSerializer):
    class Meta:
        model = DailyStateActivityReport
        fields = '__all__'
        entity_field = 'state'
        entity_type = 'state'
        level = 'state'
        children_field = 'district_data'

class WeeklyStateActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyStateActivityReportSerializer.Meta):
        model = WeeklyStateActivityReport

class MonthlyStateActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyStateActivityReportSerializer.Meta):
        model = MonthlyStateActivityReport

# Country Serializers
class DailyCountryActivityReportSerializer(BaseActivityReportSerializer):
    class Meta:
        model = DailyCountryActivityReport
        fields = '__all__'
        entity_field = 'country'
        entity_type = 'country'
        level = 'country'
        children_field = 'state_data'

class WeeklyCountryActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyCountryActivityReportSerializer.Meta):
        model = WeeklyCountryActivityReport

class MonthlyCountryActivityReportSerializer(BaseActivityReportSerializer):
    class Meta(DailyCountryActivityReportSerializer.Meta):
        model = MonthlyCountryActivityReport