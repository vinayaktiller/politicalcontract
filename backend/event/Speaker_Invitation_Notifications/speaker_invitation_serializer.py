from rest_framework import serializers
from ..models.group_speaker_invitation_notifiation import GroupSpeakerInvitationNotification
from ..groups.group_validation.serializer import GroupSerializer
from users.models.usertree import UserTree

class SpeakerInvitationSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()
    notification_message = serializers.SerializerMethodField()
    notification_data = serializers.SerializerMethodField()
    notification_number = serializers.IntegerField(source='id', read_only=True)
    notification_freshness = serializers.SerializerMethodField()

    class Meta:
        model = GroupSpeakerInvitationNotification
        fields = [
            "notification_type",
            "notification_message",
            "notification_data",
            "notification_number",
            "notification_freshness"
        ]

    def get_notification_type(self, obj):
        return "Group_Speaker_Invitation"

    def get_notification_message(self, obj):
        founder_instance = UserTree.objects.filter(id=obj.group.founder).first()
        founder_name = founder_instance.name if founder_instance else "The founder"
        return f"{founder_name} of {obj.group.name} has invited you to be a speaker. Will you accept?"

    def get_notification_data(self, obj):
        base_url = "http://localhost:8000/"  # Ensure URLs are properly prefixed
        founder_instance = UserTree.objects.filter(id=obj.group.founder).first()
        founder_name = founder_instance.name if founder_instance else "Unknown Founder"

        # Convert founder profile picture field to URL
        founder_profile_pic = ""
        if founder_instance and founder_instance.profilepic and hasattr(founder_instance.profilepic, 'url'):
            founder_profile_pic = f"{base_url}{founder_instance.profilepic.url.lstrip('/')}"
        
        # Convert group profile picture field to URL
        group_profile_pic = ""
        if obj.group.profile_pic and hasattr(obj.group.profile_pic, 'url'):
            group_profile_pic = f"{base_url}{obj.group.profile_pic.url.lstrip('/')}"
        
        profile_pic = group_profile_pic if group_profile_pic else founder_profile_pic
        profile_pic_source = "group" if group_profile_pic else "founder"

        return {
            "invitation_id": obj.id,
            "group_id": obj.group.id,
            "group_name": obj.group.name,
            "profile_picture": profile_pic,  # Now formatted as a URL
            "profile_pic_source": profile_pic_source,
            "founder_name": founder_name,
            "status": obj.status,
            "action_required": obj.status == GroupSpeakerInvitationNotification.Status.INVITED
        }

    def get_notification_freshness(self, obj):
        return not obj.seen  # Uses the `seen` field instead of status
