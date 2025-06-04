from rest_framework import serializers
from ..models.notifications import InitiationNotification
from pendingusers.serializers.pending_user_serializer import PendingUserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()
    notification_message = serializers.SerializerMethodField()
    notification_data = serializers.SerializerMethodField()
    notification_number = serializers.IntegerField(source='id', read_only=True)
    notification_freshness = serializers.BooleanField(source='viewed', read_only=True)

    class Meta:
        model = InitiationNotification
        fields = [
            "notification_type",
            "notification_message",
            "notification_data",
            "notification_number",
            "notification_freshness"
        ]

    def get_notification_type(self, obj):
        return "Initiation_Notification"

    def get_notification_message(self, obj):
        return f"Are you initiating {obj.applicant.first_name} {obj.applicant.last_name}?"

    def get_notification_data(self, obj):
        # Add any additional notification-specific data here
        return {
            **PendingUserSerializer(obj.applicant, context=self.context).data,
            "initiation_id": obj.id,
            "created_at": obj.created_at.isoformat()
        }