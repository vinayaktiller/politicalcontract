from django.db import models
from .blogsize import MicroContent, ShortEssayContent, ArticleContent
import uuid

class AnsweringQuestionBlog(models.Model):
    """Abstract base for blogs that answer questions."""
    id = models.UUIDField(primary_key=True)  # Same as BaseBlogModel.id
    questionid =models.IntegerField(null=True, blank=True)  # ID of the question being answered
    
    class Meta:
        abstract = True

class MicroAnsweringQuestionBlog(AnsweringQuestionBlog, MicroContent):
    class Meta:
        db_table = 'blog"."answering_question_blog_micro'  # Changed

class ShortEssayAnsweringQuestionBlog(AnsweringQuestionBlog, ShortEssayContent):
    class Meta:
        db_table = 'blog"."answering_question_blog_short_essay'  # Changed
        
class ArticleAnsweringQuestionBlog(AnsweringQuestionBlog, ArticleContent):
    class Meta:
        db_table = 'blog"."answering_question_blog_article'  # Changed
