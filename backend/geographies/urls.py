from django.urls import path
from . import views

urlpatterns = [
    path('countries/', views.get_countries, name='get_countries'),
    path('states/<int:country_id>/', views.get_states, name='get_states'),
    path('districts/<int:state_id>/', views.get_districts_by_state, name='get_districts_by_state'),
    path('subdistricts/<int:district_id>/', views.get_subdistricts_by_district, name='get_subdistricts_by_district'),
    path('villages/<int:subdistrict_id>/', views.get_villages_by_subdistrict, name='get_villages_by_subdistrict'),
   
]