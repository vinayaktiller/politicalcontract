from django.db import models
from django.db.models import JSONField
from geographies.models.geos import Country, State, District, Subdistrict, Village
import uuid

# Village Reports
class VillageDailyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    user_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."village_daily_report'

class VillageWeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    user_data = JSONField()
    parent_id =  models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."village_weekly_report'

class VillageMonthlyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    user_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."village_monthly_report'

# Subdistrict Reports
class SubdistrictDailyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    village_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."subdistrict_daily_report'

class SubdistrictWeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    village_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."subdistrict_weekly_report'

class SubdistrictMonthlyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    village_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."subdistrict_monthly_report'

# District Reports
class DistrictDailyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    subdistrict_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."district_daily_report'

class DistrictWeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    subdistrict_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."district_weekly_report'

class DistrictMonthlyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    subdistrict_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."district_monthly_report'

# State Reports
class StateDailyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    district_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."state_daily_report'

class StateWeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    district_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."state_weekly_report'

class StateMonthlyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    district_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."state_monthly_report'

# Country Reports
class CountryDailyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    state_data = JSONField()
    date = models.DateField()

    class Meta:
        db_table = 'report"."country_daily_report'

class CountryWeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    state_data = JSONField()

    class Meta:
        db_table = 'report"."country_weekly_report'

class CountryMonthlyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    new_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    state_data = JSONField()

    class Meta:
        db_table = 'report"."country_monthly_report'

# Cumulative Report
class CumulativeReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    REPORT_LEVEL_CHOICES = [
        ('country', 'Country'),
        ('state', 'State'),
        ('district', 'District'),
        ('subdistrict', 'Subdistrict'),
        ('village', 'Village'),
    ]

    level = models.CharField(max_length=20, choices=REPORT_LEVEL_CHOICES)
    geographical_entity = models.PositiveBigIntegerField()
    total_users = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    user_data = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'report"."cumulative_report'
        unique_together = ('level', 'geographical_entity')
        indexes = [
            models.Index(fields=['level', 'geographical_entity'])
        ]

class OverallReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    REPORT_LEVEL_CHOICES = [
        ('country', 'Country'),
        ('state', 'State'),
        ('district', 'District'),
        ('subdistrict', 'Subdistrict'),
        ('village', 'Village'),
    ]

    level = models.CharField(max_length=20, choices=REPORT_LEVEL_CHOICES)
    geographical_entity = models.PositiveBigIntegerField()
    name= models.CharField(max_length=100, blank=True, null=True)
    total_users = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    data = JSONField(blank=True, null=True)
    last30daysdata=JSONField(blank=True, null=True)
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'report"."overall_report'
        unique_together = ('level', 'geographical_entity')
        indexes = [
            models.Index(fields=['level', 'geographical_entity'])
        ]
