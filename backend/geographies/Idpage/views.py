# geographies/Idpage/views.py

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ..models.geos import Country, State, District, Subdistrict, Village
from .serializers import IDBreakdownSerializer

@extend_schema(
    # Declare that id_str is coming from the URL path
    parameters=[
        {
            "name": "id_str",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "pattern": "^[0-9]{14}$"},
            "description": "14-digit ID string"
        }
    ],
    responses=IDBreakdownSerializer
)
@api_view(['GET'])
def id_breakdown(request, id_str):
    """
    Breaks a 14‑digit ID into state, district, subdistrict, village and person_code.
    """
    # Validate ID format
    if len(id_str) != 14 or not id_str.isdigit():
        return Response(
            {"error": "Invalid ID format. Must be exactly 14 numeric digits."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Parse ID components
    state_id       = id_str[0:2]
    district_id    = id_str[0:4]
    subdistrict_id = id_str[0:6]
    village_id     = id_str[0:9]
    person_code    = id_str[9:14]

    try:
        state       = State.objects.get(id=state_id)
        district    = District.objects.get(id=district_id, state=state)
        subdistrict = Subdistrict.objects.get(id=subdistrict_id, district=district)
        village     = Village.objects.get(id=village_id, subdistrict=subdistrict)

        data = {
            "id": id_str,
            "state":       {"id": state.id,       "name": state.name},
            "district":    {"id": district.id,    "name": district.name},
            "subdistrict": {"id": subdistrict.id, "name": subdistrict.name},
            "village":     {"id": village.id,     "name": village.name},
            "person_code": person_code
        }

        # Serialize and return
        serializer = IDBreakdownSerializer(data)
        return Response(serializer.data)

    except State.DoesNotExist:
        return Response({"error": "State not found"},       status=status.HTTP_404_NOT_FOUND)
    except District.DoesNotExist:
        return Response({"error": "District not found"},    status=status.HTTP_404_NOT_FOUND)
    except Subdistrict.DoesNotExist:
        return Response({"error": "Subdistrict not found"}, status=status.HTTP_404_NOT_FOUND)
    except Village.DoesNotExist:
        return Response({"error": "Village not found"},     status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
