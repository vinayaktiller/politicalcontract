from .petitioner_serializer import PetitionerSerializer

from rest_framework import serializers
from ...models.Connectionnotification import ConnectionNotification

class NotificationSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()
    notification_message = serializers.SerializerMethodField()
    notification_data = serializers.SerializerMethodField()
    notification_number = serializers.CharField(source='id', read_only=True)
    notification_freshness = serializers.BooleanField(source='viewed', read_only=True)

    class Meta:
        model = ConnectionNotification  # Updated model reference
        fields = [
            "notification_type",
            "notification_message",
            "notification_data",
            "notification_number",
            "notification_freshness"
        ]

    def get_notification_type(self, obj):
        return "Connection_Notification"

    def get_notification_message(self, obj):
        return f"You have a new connection request from {obj.applicant.first_name} {obj.applicant.last_name}."

    def get_notification_data(self, obj):
        """
        Returns notification-specific data, pulling applicant details from PetitionerSerializer.
        """
        return {
            **PetitionerSerializer(obj.applicant, context=self.context).data,
            "connection_id": obj.id,
            "created_at": obj.created_at.isoformat()
        }
