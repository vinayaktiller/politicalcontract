# views.py
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Model
from ..models.intitationreports import (
    VillageDailyReport, VillageWeeklyReport, VillageMonthlyReport,
    SubdistrictDailyReport, SubdistrictWeeklyReport, SubdistrictMonthlyReport,
    DistrictDailyReport, DistrictWeeklyReport, DistrictMonthlyReport,
    StateDailyReport, StateWeeklyReport, StateMonthlyReport,
    CountryDailyReport, CountryWeeklyReport, CountryMonthlyReport
)
from .serializers import (
    VillageDailyReportSerializer, VillageWeeklyReportSerializer, VillageMonthlyReportSerializer,
    SubdistrictDailyReportSerializer, SubdistrictWeeklyReportSerializer, SubdistrictMonthlyReportSerializer,
    DistrictDailyReportSerializer, DistrictWeeklyReportSerializer, DistrictMonthlyReportSerializer,
    StateDailyReportSerializer, StateWeeklyReportSerializer, StateMonthlyReportSerializer,
    CountryDailyReportSerializer, CountryWeeklyReportSerializer, CountryMonthlyReportSerializer
)
from geographies.models.geos import Country


class ReportDetailView(APIView):
    MODEL_MAPPING = {
        'daily': {
            'village': VillageDailyReport,
            'subdistrict': SubdistrictDailyReport,
            'district': DistrictDailyReport,
            'state': StateDailyReport,
            'country': CountryDailyReport,
        },
        'weekly': {
            'village': VillageWeeklyReport,
            'subdistrict': SubdistrictWeeklyReport,
            'district': DistrictWeeklyReport,
            'state': StateWeeklyReport,
            'country': CountryWeeklyReport,
        },
        'monthly': {
            'village': VillageMonthlyReport,
            'subdistrict': SubdistrictMonthlyReport,
            'district': DistrictMonthlyReport,
            'state': StateMonthlyReport,
            'country': CountryMonthlyReport,
        }
    }

    SERIALIZER_MAPPING = {
        'daily': {
            'village': VillageDailyReportSerializer,
            'subdistrict': SubdistrictDailyReportSerializer,
            'district': DistrictDailyReportSerializer,
            'state': StateDailyReportSerializer,
            'country': CountryDailyReportSerializer,
        },
        'weekly': {
            'village': VillageWeeklyReportSerializer,
            'subdistrict': SubdistrictWeeklyReportSerializer,
            'district': DistrictWeeklyReportSerializer,
            'state': StateWeeklyReportSerializer,
            'country': CountryWeeklyReportSerializer,
        },
        'monthly': {
            'village': VillageMonthlyReportSerializer,
            'subdistrict': SubdistrictMonthlyReportSerializer,
            'district': DistrictMonthlyReportSerializer,
            'state': StateMonthlyReportSerializer,
            'country': CountryMonthlyReportSerializer,
        }
    }

    def get(self, request, *args, **kwargs):
        report_type = request.query_params.get('type', 'daily')
        level = request.query_params.get('level', 'country')
        report_id = request.query_params.get('report_id')

        try:
            if report_id:
                report = self.get_report_by_id(report_type, level, report_id)
            else:
                report = self.get_report_by_params(report_type, level, request.query_params)
        except (ValueError, KeyError) as e:
            return Response({'error': str(e)}, status=400)
        except Model.DoesNotExist:
            return Response({'error': 'Report not found'}, status=404)

        serializer_class = self.SERIALIZER_MAPPING[report_type][level]
        serializer = serializer_class(report)
        return Response(serializer.data)

    def get_report_by_id(self, report_type, level, report_id):
        """
        Fetch report by UUID string.
        Convert `report_id` from string to UUID object before querying.
        """
        model = self.MODEL_MAPPING[report_type][level]
        try:
            report_uuid = uuid.UUID(report_id)  # ✅ Convert string to UUID
        except ValueError:
            raise NotFound("Invalid report_id format")
        return model.objects.get(id=report_uuid)

    def get_report_by_params(self, report_type, level, params):
        model = self.MODEL_MAPPING[report_type][level]
        filters = {}

        # Time filters
        if report_type == 'daily':
            filters['date'] = params.get('date')
        elif report_type == 'weekly':
            filters['week_number'] = params.get('week')
            filters['year'] = params.get('year')
        elif report_type == 'monthly':
            filters['month'] = params.get('month')
            filters['year'] = params.get('year')

        # Geographical entity filter
        entity_id = params.get('entity_id')
        if level == 'country' and not entity_id:
            country = Country.objects.first()
            if not country:
                raise NotFound('No country found')
            entity_id = country.id

        if entity_id:
            entity_field = {
                'village': 'village_id',
                'subdistrict': 'subdistrict_id',
                'district': 'district_id',
                'state': 'state_id',
                'country': 'country_id'
            }[level]
            filters[entity_field] = entity_id

        return model.objects.get(**filters)
