# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from ..models.intitationreports import OverallReport
from geographies.models.geos import Country
from .serializers import OverallReportSerializer

class OverallReportView(APIView):
    def get(self, request):
        level = request.query_params.get('level', 'country')
        entity_id = request.query_params.get('entity_id')

        try:
            # root: list all countries
            if level == 'country' and not entity_id:
                countries = Country.objects.all()
                reports = []
                for country in countries:
                    try:
                        rep = OverallReport.objects.get(
                            level='country',
                            geographical_entity=country.id
                        )
                    except OverallReport.DoesNotExist:
                        continue
                    rep.geographical_entity = {
                        'id': country.id,
                        'name': country.name
                    }
                    reports.append(rep)
                serializer = OverallReportSerializer(reports, many=True)
                return Response(serializer.data)

            # specific entity
            if not entity_id:
                raise ValueError('Missing entity_id for non-country level')
            report = OverallReport.objects.get(level=level, geographical_entity=entity_id)
            report.geographical_entity = {
                'id': report.geographical_entity,
                'name': report.name
            }
            serializer = OverallReportSerializer(report)
            return Response(serializer.data)

        except OverallReport.DoesNotExist:
            raise NotFound('Report not found')
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
