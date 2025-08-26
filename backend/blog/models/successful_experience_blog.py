# from django.core.exceptions import ValidationError
# from django.db import models
# from .journeyblog import JourneyBlog
# import uuid
# from .blogsize import MicroContent, ShortEssayContent, ArticleContent

# class SuccessfulExperienceBlog(JourneyBlog):
#     class Meta:
#         abstract = True  # This should be a real model, not abstract
#         # Cannot use unique_together directly because 'userid' is in another table

#     def clean(self):
#         from .Baseblogmodel import BaseBlogModel
        
#         if not self.target_user:
#             raise ValidationError("target_user must be set.")

#         try:
#             base_blog = BaseBlogModel.objects.get(id=self.id)
#         except BaseBlogModel.DoesNotExist:
#             raise ValidationError("Related BaseBlogModel does not exist.")

#         if not base_blog.userid:
#             raise ValidationError("userid must be set in BaseBlogModel.")

#         # Check if any other SuccessfulExperienceBlog exists with the same userid and target_user
#         duplicate = (
#             SuccessfulExperienceBlog.objects
#             .filter(target_user=self.target_user)
#             .exclude(id=self.id)  # allow editing same record
#             .select_related(None)  # skip joins on relations
#             .filter(
#                 id__in=BaseBlogModel.objects
#                     .filter(userid=base_blog.userid)
#                     .values_list('id', flat=True)
#             )
#             .exists()
#         )

#         if duplicate:
#             raise ValidationError(
#                 f"A blog already exists for userid={base_blog.userid} and target_user={self.target_user}."
#             )

#     def save(self, *args, **kwargs):
#         # Always run clean before saving
#         self.clean()
#         super().save(*args, **kwargs)



# class MicroSuccessfulExperience(SuccessfulExperienceBlog, MicroContent):
#     class Meta(SuccessfulExperienceBlog.Meta):
#         db_table = 'blog"."successful_experience_micro'  # Changed

# class ShortEssaySuccessfulExperience(SuccessfulExperienceBlog, ShortEssayContent):
#     class Meta(SuccessfulExperienceBlog.Meta):
#         db_table = 'blog"."successful_experience_short_essay'  # Changed

# class ArticleSuccessfulExperience(SuccessfulExperienceBlog, ArticleContent):
#     class Meta(SuccessfulExperienceBlog.Meta):
#         db_table = 'blog"."successful_experience_article'  # Changed

# successful_experience_blog.py
from django.core.exceptions import ValidationError
from django.db import models
from .journeyblog import JourneyBlog
from .blogsize import MicroContent, ShortEssayContent, ArticleContent

class SuccessfulExperienceBlog(JourneyBlog):
    class Meta:
        abstract = True

    def clean(self):
        from .Baseblogmodel import BaseBlogModel
        
        if not self.target_user:
            raise ValidationError("target_user must be set.")

        try:
            base_blog = BaseBlogModel.objects.get(id=self.id)
        except BaseBlogModel.DoesNotExist:
            raise ValidationError("Related BaseBlogModel does not exist.")

        if not base_blog.userid:
            raise ValidationError("userid must be set in BaseBlogModel.")

        # Get the concrete model class for the current instance
        concrete_model = self._meta.concrete_model
        
        # Check if any other SuccessfulExperienceBlog exists with the same userid and target_user
        duplicate = (
            concrete_model.objects
            .filter(target_user=self.target_user)
            .exclude(id=self.id)  # allow editing same record
            .filter(
                id__in=BaseBlogModel.objects
                    .filter(userid=base_blog.userid)
                    .values_list('id', flat=True)
            )
            .exists()
        )

        if duplicate:
            raise ValidationError(
                f"A blog already exists for userid={base_blog.userid} and target_user={self.target_user}."
            )

    def save(self, *args, **kwargs):
        # Always run clean before saving
        self.clean()
        super().save(*args, **kwargs)

class MicroSuccessfulExperience(SuccessfulExperienceBlog, MicroContent):
    class Meta:
        db_table = 'blog"."successful_experience_micro'

class ShortEssaySuccessfulExperience(SuccessfulExperienceBlog, ShortEssayContent):
    class Meta:
        db_table = 'blog"."successful_experience_short_essay'

class ArticleSuccessfulExperience(SuccessfulExperienceBlog, ArticleContent):
    class Meta:
        db_table = 'blog"."successful_experience_article'