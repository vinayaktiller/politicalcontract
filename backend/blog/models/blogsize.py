from django.db import models

class MicroContent(models.Model):
    """Content with a small character limit like Twitter."""
    content = models.CharField(max_length=280)  # Classic Twitter limit

    class Meta:
        abstract = True


class ShortEssayContent(models.Model):
    """Content limited to ~500 words (~3200 characters)."""
    content = models.CharField(max_length=3200)

    class Meta:
        abstract = True


class ArticleContent(models.Model):
    """Content limited to ~3–4 pages (~12,000 characters)."""
    content = models.TextField(max_length=12000)

    class Meta:
        abstract = True
