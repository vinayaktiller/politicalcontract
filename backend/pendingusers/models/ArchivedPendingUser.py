from django.db import models

class ArchivedPendingUser(models.Model):
    gmail = models.EmailField()
    initiator_id = models.BigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("not_sent", "Not Sent"),
            ("not_seen", "Not Seen"),
            ("not_reacted", "Not Reacted"),
            ("rejected", "Rejected"),
        ],
    )
    archived_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gmail} - {self.status} - {self.initiator_id} - {self.archived_at}"
    class Meta:
        db_table = 'pendinguser"."archivedpendinguser'
