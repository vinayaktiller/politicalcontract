# serializers.py
from rest_framework import serializers
from ..models.intitationreports import (
    VillageDailyReport, VillageWeeklyReport, VillageMonthlyReport,
    SubdistrictDailyReport, SubdistrictWeeklyReport, SubdistrictMonthlyReport,
    DistrictDailyReport, DistrictWeeklyReport, DistrictMonthlyReport,
    StateDailyReport, StateWeeklyReport, StateMonthlyReport,
    CountryDailyReport, CountryWeeklyReport, CountryMonthlyReport
)

class BaseReportSerializer(serializers.ModelSerializer):
    geographical_entity = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    parent_info = serializers.SerializerMethodField()
    children_data = serializers.SerializerMethodField()

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

    class Meta:
        abstract = True

# Village Serializers
class VillageDailyReportSerializer(BaseReportSerializer):
    class Meta:
        model = VillageDailyReport
        fields = '__all__'
        entity_field = 'village'
        entity_type = 'village'
        level = 'village'
        children_field = 'user_data'

class VillageWeeklyReportSerializer(BaseReportSerializer):
    class Meta(VillageDailyReportSerializer.Meta):
        model = VillageWeeklyReport

class VillageMonthlyReportSerializer(BaseReportSerializer):
    class Meta(VillageDailyReportSerializer.Meta):
        model = VillageMonthlyReport

# Subdistrict Serializers
class SubdistrictDailyReportSerializer(BaseReportSerializer):
    class Meta:
        model = SubdistrictDailyReport
        fields = '__all__'
        entity_field = 'subdistrict'
        entity_type = 'subdistrict'
        level = 'subdistrict'
        children_field = 'village_data'

class SubdistrictWeeklyReportSerializer(BaseReportSerializer):
    class Meta(SubdistrictDailyReportSerializer.Meta):
        model = SubdistrictWeeklyReport

class SubdistrictMonthlyReportSerializer(BaseReportSerializer):
    class Meta(SubdistrictDailyReportSerializer.Meta):
        model = SubdistrictMonthlyReport

# District Serializers
class DistrictDailyReportSerializer(BaseReportSerializer):
    class Meta:
        model = DistrictDailyReport
        fields = '__all__'
        entity_field = 'district'
        entity_type = 'district'
        level = 'district'
        children_field = 'subdistrict_data'

class DistrictWeeklyReportSerializer(BaseReportSerializer):
    class Meta(DistrictDailyReportSerializer.Meta):
        model = DistrictWeeklyReport

class DistrictMonthlyReportSerializer(BaseReportSerializer):
    class Meta(DistrictDailyReportSerializer.Meta):
        model = DistrictMonthlyReport

# State Serializers
class StateDailyReportSerializer(BaseReportSerializer):
    class Meta:
        model = StateDailyReport
        fields = '__all__'
        entity_field = 'state'
        entity_type = 'state'
        level = 'state'
        children_field = 'district_data'

class StateWeeklyReportSerializer(BaseReportSerializer):
    class Meta(StateDailyReportSerializer.Meta):
        model = StateWeeklyReport

class StateMonthlyReportSerializer(BaseReportSerializer):
    class Meta(StateDailyReportSerializer.Meta):
        model = StateMonthlyReport

# Country Serializers
class CountryDailyReportSerializer(BaseReportSerializer):
    class Meta:
        model = CountryDailyReport
        fields = '__all__'
        entity_field = 'country'
        entity_type = 'country'
        level = 'country'
        children_field = 'state_data'

class CountryWeeklyReportSerializer(BaseReportSerializer):
    class Meta(CountryDailyReportSerializer.Meta):
        model = CountryWeeklyReport

class CountryMonthlyReportSerializer(BaseReportSerializer):
    class Meta(CountryDailyReportSerializer.Meta):
        model = CountryMonthlyReport