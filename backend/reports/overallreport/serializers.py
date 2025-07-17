from rest_framework import serializers
from ..models.intitationreports import OverallReport

class GeographicalEntitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class OverallReportSerializer(serializers.ModelSerializer):
    geographical_entity = GeographicalEntitySerializer()
    children = serializers.SerializerMethodField()

    class Meta:
        model = OverallReport
        fields = [
            'id',
            'level',
            'geographical_entity',
            'total_users',
            'last_updated',
            'data',
            'last30daysdata',
            'parent_id',
            'children'
        ]

    def get_children(self, obj):
        children = OverallReport.objects.filter(parent_id=obj.id)
        return [
            {
                'id': child.id,
                'level': child.level,
                'geographical_entity': {
                    'id': child.geographical_entity,
                    'name': child.name
                },
                'total_users': child.total_users
            }
            for child in children
        ]
