# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Country(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    offline_population = models.BigIntegerField(blank=True, null=True)
    online_population = models.BigIntegerField(blank=True, null=True)
    number_of_states = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'country'


class District(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    online_population = models.IntegerField(blank=True, null=True)
    offline_population = models.IntegerField(blank=True, null=True)
    state = models.ForeignKey('State', models.DO_NOTHING, blank=True, null=True)
    number_of_subdistricts = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'district'


class State(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, models.DO_NOTHING)
    online_population = models.IntegerField(blank=True, null=True)
    offline_population = models.IntegerField(blank=True, null=True)
    number_of_districts = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'state'


class Subdistrict(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    online_population = models.IntegerField(blank=True, null=True)
    offline_population = models.IntegerField(blank=True, null=True)
    district = models.ForeignKey(District, models.DO_NOTHING, blank=True, null=True)
    number_of_villages = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subdistrict'


class Village(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=100, blank=True, null=True)
    online_population = models.IntegerField(blank=True, null=True)
    offline_population = models.IntegerField(blank=True, null=True)
    subdistrict = models.ForeignKey(Subdistrict, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'village'
