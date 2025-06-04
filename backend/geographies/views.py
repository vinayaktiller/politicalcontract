from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from prometheus_client import Counter
from django.db import connection
from .models.geos import Country, State, District, Subdistrict, Village
from .serializers import CountrySerializer, StateSerializer, DistrictSerializer, SubDistrictSerializer, VillageSerializer

# Define Prometheus counters for all API functions
api_call_counter = Counter('api_requests_total', 'Total number of API calls per endpoint', ['endpoint'])
db_query_counter = Counter('database_queries_total', 'Total number of database queries executed per endpoint', ['endpoint'])

@extend_schema(responses=CountrySerializer(many=True))
@api_view(['GET'])
def get_countries(request):
    api_call_counter.labels(endpoint='get_countries').inc()
    countries = Country.objects.all()
    query_count = len(connection.queries)
    db_query_counter.labels(endpoint='get_countries').inc(query_count)
    serializer = CountrySerializer(countries, many=True)
    return Response(serializer.data)

@extend_schema(parameters=[{'name': 'country_id', 'required': True, 'type': 'integer'}], responses=StateSerializer(many=True))
@api_view(['GET'])
def get_states(request, country_id):
    api_call_counter.labels(endpoint='get_states').inc()
    states = State.objects.filter(country_id=country_id)
    query_count = len(connection.queries)
    db_query_counter.labels(endpoint='get_states').inc(query_count)
    serializer = StateSerializer(states, many=True)
    return Response(serializer.data)

@extend_schema(parameters=[{'name': 'state_id', 'required': True, 'type': 'integer'}], responses=DistrictSerializer(many=True))
@api_view(['GET'])
def get_districts_by_state(request, state_id):
    api_call_counter.labels(endpoint='get_districts_by_state').inc()
    districts = District.objects.filter(state_id=state_id)
    query_count = len(connection.queries)
    db_query_counter.labels(endpoint='get_districts_by_state').inc(query_count)
    serializer = DistrictSerializer(districts, many=True)
    return Response(serializer.data)

@extend_schema(parameters=[{'name': 'district_id', 'required': True, 'type': 'integer'}], responses=SubDistrictSerializer(many=True))
@api_view(['GET'])
def get_subdistricts_by_district(request, district_id):
    api_call_counter.labels(endpoint='get_subdistricts_by_district').inc()
    subdistricts = Subdistrict.objects.filter(district_id=district_id)
    query_count = len(connection.queries)
    db_query_counter.labels(endpoint='get_subdistricts_by_district').inc(query_count)
    serializer = SubDistrictSerializer(subdistricts, many=True)
    return Response(serializer.data)

@extend_schema(parameters=[{'name': 'subdistrict_id', 'required': True, 'type': 'integer'}], responses=VillageSerializer(many=True))
@api_view(['GET'])
def get_villages_by_subdistrict(request, subdistrict_id):
    api_call_counter.labels(endpoint='get_villages_by_subdistrict').inc()
    villages = Village.objects.filter(subdistrict_id=subdistrict_id)
    query_count = len(connection.queries)
    db_query_counter.labels(endpoint='get_villages_by_subdistrict').inc(query_count)
    serializer = VillageSerializer(villages, many=True)
    return Response(serializer.data)
