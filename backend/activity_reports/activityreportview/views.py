# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Model
from ..models import (
    DailyVillageActivityReport, WeeklyVillageActivityReport, MonthlyVillageActivityReport,
    DailySubdistrictActivityReport, WeeklySubdistrictActivityReport, MonthlySubdistrictActivityReport,
    DailyDistrictActivityReport, WeeklyDistrictActivityReport, MonthlyDistrictActivityReport,
    DailyStateActivityReport, WeeklyStateActivityReport, MonthlyStateActivityReport,
    DailyCountryActivityReport, WeeklyCountryActivityReport, MonthlyCountryActivityReport
)
from .serializers import *
from geographies.models.geos import Country

class ActivityReportDetailView(APIView):
    MODEL_MAPPING = {
        'daily': {
            'village': DailyVillageActivityReport,
            'subdistrict': DailySubdistrictActivityReport,
            'district': DailyDistrictActivityReport,
            'state': DailyStateActivityReport,
            'country': DailyCountryActivityReport,
        },
        'weekly': {
            'village': WeeklyVillageActivityReport,
            'subdistrict': WeeklySubdistrictActivityReport,
            'district': WeeklyDistrictActivityReport,
            'state': WeeklyStateActivityReport,
            'country': WeeklyCountryActivityReport,
        },
        'monthly': {
            'village': MonthlyVillageActivityReport,
            'subdistrict': MonthlySubdistrictActivityReport,
            'district': MonthlyDistrictActivityReport,
            'state': MonthlyStateActivityReport,
            'country': MonthlyCountryActivityReport,
        }
    }
    
    SERIALIZER_MAPPING = {
        'daily': {
            'village': DailyVillageActivityReportSerializer,
            'subdistrict': DailySubdistrictActivityReportSerializer,
            'district': DailyDistrictActivityReportSerializer,
            'state': DailyStateActivityReportSerializer,
            'country': DailyCountryActivityReportSerializer,
        },
        'weekly': {
            'village': WeeklyVillageActivityReportSerializer,
            'subdistrict': WeeklySubdistrictActivityReportSerializer,
            'district': WeeklyDistrictActivityReportSerializer,
            'state': WeeklyStateActivityReportSerializer,
            'country': WeeklyCountryActivityReportSerializer,
        },
        'monthly': {
            'village': MonthlyVillageActivityReportSerializer,
            'subdistrict': MonthlySubdistrictActivityReportSerializer,
            'district': MonthlyDistrictActivityReportSerializer,
            'state': MonthlyStateActivityReportSerializer,
            'country': MonthlyCountryActivityReportSerializer,
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
        model = self.MODEL_MAPPING[report_type][level]
        return model.objects.get(id=report_id)
    
    def get_report_by_params(self, report_type, level, params):
        model = self.MODEL_MAPPING[report_type][level]
        filters = {}
        
        # Time filters
        if report_type == 'daily':
            date_param = params.get('date')
            if not date_param:
                raise ValueError("Date parameter is required for daily reports")
            filters['date'] = date_param
        elif report_type == 'weekly':
            week_param = params.get('week')
            year_param = params.get('year')
            if not week_param or not year_param:
                raise ValueError("Week and year parameters are required for weekly reports")
            filters['week_number'] = week_param
            filters['year'] = year_param
        elif report_type == 'monthly':
            month_param = params.get('month')
            year_param = params.get('year')
            if not month_param or not year_param:
                raise ValueError("Month and year parameters are required for monthly reports")
            filters['month'] = month_param
            filters['year'] = year_param
        
        # Geographical entity filter
        entity_id = params.get('entity_id')
        if level == 'country' and not entity_id:
            # Default to first country if not specified
            country = Country.objects.first()
            if not country:
                raise NotFound('No country found in database')
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
        
        try:
            return model.objects.get(**filters)
        except model.MultipleObjectsReturned:
            # Handle case where multiple reports exist (shouldn't happen but safe guard)
            return model.objects.filter(**filters).latest('date' if report_type == 'daily' else 'year')