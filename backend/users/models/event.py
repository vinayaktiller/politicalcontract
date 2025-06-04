from django.db import models
from geographies.models.geos import Country, State, District, Subdistrict, Village
from .eventname import EventName
from .usertree import UserTree
class event (models.Model):
    eventname= models.ForeignKey(EventName, on_delete=models.DO_NOTHING, null=True, blank=True)
    eventid= models.BigIntegerField(null=True, blank=True)
    speakers= models.ForeignKey(UserTree, on_delete=models.DO_NOTHING, null=True, blank=True)
    organizer= models.ForeignKey(UserTree, on_delete=models.DO_NOTHING, null=True, blank=True)
    agents= models.ForeignKey(UserTree, on_delete=models.DO_NOTHING, null=True, blank=True)
    particpants= models.ForeignKey(UserTree, on_delete=models.DO_NOTHING, null=True, blank=True)
    members= models.ForeignKey(UserTree, on_delete=models.DO_NOTHING, null=True, blank=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True)
    information= models.TextField(null=True, blank=True)
    eventdate= models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'userschema"."eventname' 
