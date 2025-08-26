import logging
from django.db import transaction
from pendingusers.models.notifications import InitiationNotification
from users.models.Connectionnotification import ConnectionNotification
from event.models.group_speaker_invitation_notifiation import GroupSpeakerInvitationNotification

from pendingusers.services.send_notification_to_initiator import send_notification_to_initiator
from users.makingconnections.services.send_notfication_to_connection import send_notification_to_connection
from users.makingconnections.services.send_status_to_applicant import send_status_to_applicant
from event.Speaker_Invitation_Notifications.send_speaker_invitation import send_speaker_invitation


logger = logging.getLogger(__name__)

def handle_user_notifications_on_login(user):
    """
    Handle pending notifications for a user upon login.
    
    Checks for:
    1. InitiationNotifications where user is initiator
    2. ConnectionNotifications where user is either:
       - connection (receiver) 
       - applicant (sender)
    
    Triggers appropriate notification services based on user's role in notifications.
    
    Args:
        user: Authenticated user instance
    """
    logger.info(f"Processing notifications for user {user.id}")
    
    try:
        # Process InitiationNotifications
        _process_initiation_notifications(user)
        
        # Process ConnectionNotifications
        _process_connection_notifications(user)

        # Process GroupSpeakerInvitationNotifications
        _process_speaker_invitation_notifications(user)
           


        logger.info(f"Completed notification processing for user {user.id}")
    except Exception as e:
        logger.critical(f"Critical failure processing notifications for user {user.id}: {str(e)}")

def _process_initiation_notifications(user):
    """Process InitiationNotifications where user is the initiator"""
    notifications = InitiationNotification.objects.filter(
        initiator_id=user.id,
        reacted=False
    )
    
    logger.debug(f"Found {notifications.count()} pending InitiationNotifications for initiator {user.id}")
    
    for notification in notifications:
        try:
            with transaction.atomic():
                logger.info(f"Sending initiator notification for InitiationNotification {notification.id}")
                send_notification_to_initiator(notification)
                logger.debug(f"Successfully sent initiator notification for {notification.id}")
        except Exception as e:
            logger.error(f"Failed to send initiator notification for {notification.id}: {str(e)}")

def _process_connection_notifications(user):
    """Process ConnectionNotifications where user is connection or applicant"""
    # As connection (receiver)
    as_connection = ConnectionNotification.objects.filter(
        connection=user,
        reacted=False
    )
    
    logger.debug(f"Found {as_connection.count()} ConnectionNotifications as connection for user {user.id}")
    
    for notification in as_connection:
        try:
            with transaction.atomic():
                logger.info(f"Sending connection notification for ConnectionNotification {notification.id}")
                send_notification_to_connection(notification)
                logger.debug(f"Successfully sent connection notification for {notification.id}")
        except Exception as e:
            logger.error(f"Failed to send connection notification for {notification.id}: {str(e)}")
    
    # As applicant (sender)
    as_applicant = ConnectionNotification.objects.filter(
        applicant=user,
        completed=False
    )
    
    logger.debug(f"Found {as_applicant.count()} ConnectionNotifications as applicant for user {user.id}")
    
    for notification in as_applicant:
        try:
            with transaction.atomic():
                logger.info(f"Sending applicant status for ConnectionNotification {notification.id}")
                send_status_to_applicant(notification)
                logger.debug(f"Successfully sent applicant status for {notification.id}")
        except Exception as e:
            logger.error(f"Failed to send applicant status for {notification.id}: {str(e)}")


def _process_speaker_invitation_notifications(user):
    """Process GroupSpeakerInvitationNotification where user is the invited speaker"""
    # Assuming `speaker` is a Petitioner linked to `user`
    notifications = GroupSpeakerInvitationNotification.objects.filter(
        speaker=user,
    )
    for notification in notifications:
        try:
            with transaction.atomic():
                # send the push/in-app invitation
                send_speaker_invitation(notification)
                # mark notification as seen so it isn't re-sent
                notification.mark_as_seen()
        except Exception as e:
            logger.error(f"Failed to send speaker invitation {notification.id}: {e}")
