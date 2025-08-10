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
    """Micro blog that answers a question."""
    class Meta:
        db_table = 'blog"."micro_answering_question_blog'

class ShortEssayAnsweringQuestionBlog(AnsweringQuestionBlog, ShortEssayContent):
    """Short essay blog that answers a question."""
    class Meta:
        db_table = 'blog"."short_essay_answering_question_blog'
        
class ArticleAnsweringQuestionBlog(AnsweringQuestionBlog, ArticleContent):
    """Article blog that answers a question."""
    class Meta:
        db_table = 'blog"."article_answering_question_blog'

