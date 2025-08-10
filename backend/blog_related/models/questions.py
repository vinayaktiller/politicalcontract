from django.db import models

class Question(models.Model):
    text = models.CharField(max_length=500)
    author_id = models.BigIntegerField(null=True, blank=True)  # store user ID directly
    is_approved = models.BooleanField(default=False)
    
    rank = models.PositiveIntegerField()  # display order (1 = highest priority)
    activity_score = models.PositiveIntegerField(default=0)  # engagement metric

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.rank} - {self.text[:60]}"
    class Meta:
        ordering = ['rank', 'created_at']
        db_table = 'blog_related"."questions'  # Use double quotes for PostgreSQL compatibility
