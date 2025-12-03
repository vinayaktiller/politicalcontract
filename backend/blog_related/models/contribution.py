from blog.models.blogsize import MicroContent, ShortEssayContent, ArticleContent
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

class Contribution(models.Model):
    CONTRIBUTION_TYPES = [
        ('article', 'Article'),
        ('video', 'Video'),
        ('podcast', 'Podcast'),
        ('design', 'Design/Artwork'),
        ('research', 'Research Paper'),
        ('other', 'Other'),
        ('none', 'None')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.URLField(max_length=400, null=True, blank=True, unique=True)
    title = models.CharField(max_length=400, null=True, blank=True)
    discription = models.TextField(null=True, blank=True)
    type = models.CharField(
        max_length=20, 
        choices=CONTRIBUTION_TYPES, 
        default='none',
        null=True, 
        blank=True
    )
    owner = models.BigIntegerField(null=True, blank=True)
    teammembers = ArrayField(
        models.BigIntegerField(),
        default=list,
        null=True, blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    byconsumer= models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blog_related"."contribution'        
    
    def __str__(self):
        return f"Contribution {self.id} by User {self.owner}"