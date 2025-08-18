# models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid
from .journeyblog import JourneyBlog
from .blogsize import MicroContent, ShortEssayContent, ArticleContent

class ReportReference(models.Model):
    """Abstract model for report references in blogs."""
    REPORT_TYPE_CHOICES = [

        # Activity Reports
        ('activity_reports.DailyVillageActivityReport', 'Daily Village Activity Report'),
        ('activity_reports.WeeklyVillageActivityReport', 'Weekly Village Activity Report'),
        ('activity_reports.MonthlyVillageActivityReport', 'Monthly Village Activity Report'),
        ('activity_reports.DailySubdistrictActivityReport', 'Daily Subdistrict Activity Report'),
        ('activity_reports.WeeklySubdistrictActivityReport', 'Weekly Subdistrict Activity Report'),
        ('activity_reports.MonthlySubdistrictActivityReport', 'Monthly Subdistrict Activity Report'),
        ('activity_reports.DailyDistrictActivityReport', 'Daily District Activity Report'),
        ('activity_reports.WeeklyDistrictActivityReport', 'Weekly District Activity Report'),
        ('activity_reports.MonthlyDistrictActivityReport', 'Monthly District Activity Report'),
        ('activity_reports.DailyStateActivityReport', 'Daily State Activity Report'),
        ('activity_reports.WeeklyStateActivityReport', 'Weekly State Activity Report'),
        ('activity_reports.MonthlyStateActivityReport', 'Monthly State Activity Report'),
        ('activity_reports.DailyCountryActivityReport', 'Daily Country Activity Report'),
        ('activity_reports.WeeklyCountryActivityReport', 'Weekly Country Activity Report'),
        ('activity_reports.MonthlyCountryActivityReport', 'Monthly Country Activity Report'),
        
        # User Reports
        ('report.VillageDailyReport', 'Village Daily Report'),
        ('report.VillageWeeklyReport', 'Village Weekly Report'),
        ('report.VillageMonthlyReport', 'Village Monthly Report'),
        ('report.SubdistrictDailyReport', 'Subdistrict Daily Report'),
        ('report.SubdistrictWeeklyReport', 'Subdistrict Weekly Report'),
        ('report.SubdistrictMonthlyReport', 'Subdistrict Monthly Report'),
        ('report.DistrictDailyReport', 'District Daily Report'),
        ('report.DistrictWeeklyReport', 'District Weekly Report'),
        ('report.DistrictMonthlyReport', 'District Monthly Report'),
        ('report.StateDailyReport', 'State Daily Report'),
        ('report.StateWeeklyReport', 'State Weekly Report'),
        ('report.StateMonthlyReport', 'State Monthly Report'),
        ('report.CountryDailyReport', 'Country Daily Report'),
        ('report.CountryWeeklyReport', 'Country Weekly Report'),
        ('report.CountryMonthlyReport', 'Country Monthly Report'),
        ('report.CumulativeReport', 'Cumulative Report'),
        ('report.OverallReport', 'Overall Report'),
    ]

    
    id = models.UUIDField(primary_key=True) 
    report_type = models.CharField(
        max_length=100, 
        choices=REPORT_TYPE_CHOICES,
        blank=True,
        null=True
    )
    report_id = models.UUIDField() 

    class Meta:
        abstract = True
class micro_report_insight_blog(ReportReference, MicroContent):
    class Meta:
        db_table = 'blog"."report_insight_blog_micro'  # Changed

class short_essay_report_insight_blog(ReportReference, ShortEssayContent):
    class Meta:
        db_table = 'blog"."report_insight_blog_short_essay'  # Changed

class article_report_insight_blog(ReportReference, ArticleContent):
    class Meta:
        db_table = 'blog"."report_insight_blog_article'  # Changed
