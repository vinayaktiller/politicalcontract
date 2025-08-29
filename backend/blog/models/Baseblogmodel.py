import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

class BaseBlogModel(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Using UUID instead of BigAutoField
    userid = models.BigIntegerField(null=True, blank=True)  # User ID associated with the blog entry
    likes = ArrayField(models.BigIntegerField(), blank=True, default=list)
    dislikes = ArrayField(models.BigIntegerField(), blank=True, default=list)
    relevant_count = ArrayField(models.BigIntegerField(), blank=True, default=list)
    irrelevant_count = ArrayField(models.BigIntegerField(), blank=True, default=list)
    shares = ArrayField(models.BigIntegerField(), blank=True, default=list)
    type= models.CharField(max_length=50, blank=True, null=True)  # Type of the blog entry
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = ArrayField(models.UUIDField(), blank=True, default=list)


    class Meta:
         db_table = 'blog"."base_blog_model'