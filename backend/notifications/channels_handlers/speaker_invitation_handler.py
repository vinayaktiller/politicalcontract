# notifications/channels_handlers/speaker_invitation_handler.py
import json
from asgiref.sync import sync_to_async
from event.models.group_speaker_invitation_notifiation import GroupSpeakerInvitationNotification

async def handle_speaker_invitation(consumer, data):
    action = data.get("messagetype")
    invitation_id = data.get("invitation_id")
    print(f" invitation_id: {invitation_id}, action: {action}")
    
    try:
        # Get the invitation
        invitation = await sync_to_async(GroupSpeakerInvitationNotification.objects.get)(id=invitation_id)
        
        # Ensure the current user is the invited speaker
        # if consumer.scope["user"].id != invitation.speaker.id:
        #     await consumer.send(json.dumps({"error": "Unauthorized action"}))
        #     return
        
        if action == "accept":
            await sync_to_async(invitation.mark_as_accepted)()
        elif action == "reject":
            await sync_to_async(invitation.mark_as_rejected)()
        elif action == "update_seen_status":
            await sync_to_async(invitation.mark_as_seen)()
        else:
            await consumer.send(json.dumps({"error": "Invalid action"}))
        
        await consumer.send(json.dumps({"success": f"Invitation {action}ed"}))
        
    except GroupSpeakerInvitationNotification.DoesNotExist:
        await consumer.send(json.dumps({"error": "Invitation not found"}))