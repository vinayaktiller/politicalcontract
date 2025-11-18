from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField

class UserSharedBlog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    userid = models.BigIntegerField()  # User who shared the blog
    shared_blog_id = models.UUIDField()  # The base blog ID that was shared
    shared_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: if you want to track the original author of the shared content
    original_author_id = models.BigIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'blog"."user_shared_blogs'
        indexes = [
            models.Index(fields=['userid', 'shared_at']),
            models.Index(fields=['shared_blog_id']),
        ]
    
    def __str__(self):
        return f"User {self.userid} shared blog {self.shared_blog_id}"