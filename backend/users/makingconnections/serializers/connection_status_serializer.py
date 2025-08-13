from rest_framework import serializers
from ...models.Connectionnotification import ConnectionNotification
from .petitioner_serializer import PetitionerSerializer  # Assuming this is the correct import path
class ConnectionStatusSerializer(serializers.ModelSerializer):
    notification_type = serializers.SerializerMethodField()
    notification_message = serializers.SerializerMethodField()
    notification_data = serializers.SerializerMethodField()
    notification_number = serializers.CharField(source='id', read_only=True)
    notification_freshness = serializers.SerializerMethodField()  # Override with custom logic

    class Meta:
        model = ConnectionNotification
        fields = [
            "notification_type",
            "notification_message",
            "notification_data",
            "notification_number",
            "notification_freshness"
        ]

    def get_notification_type(self, obj):
        return "Connection_Status"

    def get_notification_message(self, obj):
        """
        Retrieves the status message based on the notification's status.
        """
        return obj.STATUS_MESSAGES.get(obj.status, "Unknown status")

    def get_notification_data(self, obj):
        """
        Returns connection-specific data including applicant details and status.
        """
        petitioner = obj.connection
        profile_picture = PetitionerSerializer().get_profile_picture(petitioner) if petitioner else None
        return {

            "connection_id": obj.id,
            "applicant_name": f"{obj.connection.first_name} {obj.connection.last_name}",
            "profile_picture": profile_picture,
            "status": obj.status,
            "status_message": obj.STATUS_MESSAGES.get(obj.status, "Unknown status"),
            
        }

    def get_notification_freshness(self, obj):
        """
        Always returns False, overriding the actual 'viewed' field.
        """
        return False
