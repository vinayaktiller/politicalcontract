from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # who wrote it
    user_id = models.BigIntegerField(null=False, blank=False, db_index=True)

    # parent comment id (UUID) — not a FK per your spec
    parent = models.UUIDField(null=True, blank=True, db_index=True)

    # parent type (can be 'blog' or 'comment')
    PARENT_TYPE_CHOICES = [
        ("blog", "Blog"),
        ("comment", "Comment"),
    ]
    parent_type = models.CharField(
        max_length=20,
        choices=PARENT_TYPE_CHOICES,
        null=False,
        blank=False,
        db_index=True,
    )

    # reactions
    likes = ArrayField(models.BigIntegerField(), blank=True, default=list)
    dislikes = ArrayField(models.BigIntegerField(), blank=True, default=list)

    # content
    text = models.CharField(max_length=3200)

    # children comment UUIDs
    children = ArrayField(models.UUIDField(), blank=True, default=list)

    # bookkeeping
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog"."comment'
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Comment({self.id}) by {self.user_id}"
    def get_root_blog_id(self):
        """
        Traverse up the comment hierarchy to find the root blog ID
        """
        current = self
        while current.parent_type != 'blog':
            try:
                current = Comment.objects.get(id=current.parent)
            except Comment.DoesNotExist:
                return None
        return current.parent