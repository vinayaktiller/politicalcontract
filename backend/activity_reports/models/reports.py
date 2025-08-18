import uuid
from django.db import models
from django.db.models import JSONField
from geographies.models.geos import Village, Subdistrict, District, State, Country

# ======================s
# VILLAGE ACTIVITY REPORTS
# ======================
class DailyVillageActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    user_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."daily_village_activity_report'


class WeeklyVillageActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    user_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."weekly_village_activity_report'


class MonthlyVillageActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    user_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."monthly_village_activity_report'


# ======================
# SUBDISTRICT ACTIVITY REPORTS
# ======================
class DailySubdistrictActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    village_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."daily_subdistrict_activity_report'


class WeeklySubdistrictActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    village_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."weekly_subdistrict_activity_report'


class MonthlySubdistrictActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    village_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."monthly_subdistrict_activity_report'


# ======================
# DISTRICT ACTIVITY REPORTS
# ======================
class DailyDistrictActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    subdistrict_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."daily_district_activity_report'


class WeeklyDistrictActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    subdistrict_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."weekly_district_activity_report'


class MonthlyDistrictActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    subdistrict_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."monthly_district_activity_report'


# ======================
# STATE ACTIVITY REPORTS
# ======================
class DailyStateActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    district_data = JSONField()
    date = models.DateField()
    parent_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."daily_state_activity_report'


class WeeklyStateActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    district_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."weekly_state_activity_report'


class MonthlyStateActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    district_data = JSONField()
    parent_id = models.UUIDField(null=True, blank=True)
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."monthly_state_activity_report'


# ======================
# COUNTRY ACTIVITY REPORTS
# ======================
class DailyCountryActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    state_data = JSONField()
    date = models.DateField()
    

    class Meta:
        db_table = 'activity_reports"."daily_country_activity_report'


class WeeklyCountryActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    week_number = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    week_start_date = models.DateField()
    week_last_date = models.DateField()
    state_data = JSONField()
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."weekly_country_activity_report'


class MonthlyCountryActivityReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    active_users = models.PositiveIntegerField(default=0)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    last_date = models.DateField()
    state_data = JSONField()
    additional_info = JSONField(null=True, blank=True)

    class Meta:
        db_table = 'activity_reports"."monthly_country_activity_report'
