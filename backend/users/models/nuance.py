# from django.db import models

# class InitiationNuance(models.Model):
#     userid = models.BigIntegerField(primary_key=True)
#     initiator = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='initiated_by')
#     initiatecount = models.IntegerField(default=0)
#     agent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
#     memberscount = models.IntegerField(default=0)
#     group_agent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_agents')
#     groupmemberscount = models.IntegerField(default=0)
#     speaker = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='speakers')
#     audiencecount = models.IntegerField(default=0)
#     friendscount = models.IntegerField(default=0)

#     def __str__(self):
#         return f"User {self.userid}"
#     class Meta:
#         db_table = 'userschema"."initiatenuance'  # Schema-aware table name
