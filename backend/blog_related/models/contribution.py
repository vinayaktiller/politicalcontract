from blog.models.blogsize import MicroContent, ShortEssayContent, ArticleContent
import uuid
from django.db import models

class Contribution(models.Model):

    """
    Abstract base class for contributions to blogs.
    """

    id = models.UUIDField(primary_key=True) # Same as BaseBlogModel.id
    link = models.URLField(max_length=400, null=True, blank=True, unique=True)  # Link to the contribution
    title = models.CharField(max_length=400, null=True, blank=True)  # Title of the contribution
    discription = models.TextField(null=True, blank=True)  # Description of the contribution

    class Meta:
        db_table = 'blog_related"."contribution'        

    def __str__(self):
        return f"Contribution {self.id} by User {self.user_id}"

# class MicroContribution(Contribution, MicroContent):
#     """Micro contribution to a blog."""
#     class Meta:
#         db_table = 'blog_related"."contribution_micro'
# class ShortEssayContribution(Contribution, ShortEssayContent):
#     """Short essay contribution to a blog."""
#     class Meta:
#         db_table = 'blog_related"."contribution_short_essay'
# class ArticleContribution(Contribution, ArticleContent):
#     """Article contribution to a blog."""
#     class Meta:
#         db_table = 'blog_related"."contribution_article'