from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField

class BlogLoad(models.Model):
    userid = models.BigIntegerField(primary_key=True)
    loaded_blogs = ArrayField(models.UUIDField(), blank=True, default=list)
    modified_blogs = ArrayField(models.UUIDField(), blank=True, default=list)
    new_blogs = ArrayField(models.UUIDField(), blank=True, default=list)
    deleted_blogs = ArrayField(models.UUIDField(), blank=True, default=list)
    outdated=models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.userid)
    class Meta:
        db_table = 'blog"."blog_load'

