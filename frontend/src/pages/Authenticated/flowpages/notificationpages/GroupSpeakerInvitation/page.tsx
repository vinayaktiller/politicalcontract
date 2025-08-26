import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import ProfileImage from './components/ProfileImage';
import { AppDispatch, RootState } from '../../../../../store';
import { markAsViewed, removeNotification } from '../notification_state/notificationsSlice';
import { sendWebSocketMessage } from '../notification_state/notificationsThunk';
import { 
  GroupSpeakerInvitationNotification,
  GroupSpeakerInvitationNotificationData
} from '../notification_state/notificationsTypes';
import './GroupSpeakerInvitation.css';

const GroupSpeakerInvitation: React.FC = () => {
  const { notificationNumber } = useParams<{ notificationNumber: string }>();
  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();

  // Filter notifications and cast to specific type
  const groupSpeakerNotifications = useSelector((state: RootState) =>
    state.notifications.notifications.filter(
      (n): n is GroupSpeakerInvitationNotification => 
        n.notification_type === "Group_Speaker_Invitation"
    )
  );

  // Find the specific notification with type safety
  const notification = groupSpeakerNotifications.find(
    n => n.id === Number(notificationNumber)
  );

  const currentIndex = groupSpeakerNotifications.findIndex(
    n => n.id === Number(notificationNumber)
  );

  useEffect(() => {
    if (notification && !notification.notification_freshness) {
      dispatch(markAsViewed(notification.id));
      dispatch(
        sendWebSocketMessage("Group_Speaker_Invitation", "update_seen_status", {
          notificationId: notification.notification_number,
          seen: true
        })
      );
    }
  }, [dispatch, notification]);

  const handleNavigation = (direction: 'prev' | 'next') => {
    const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex >= 0 && newIndex < groupSpeakerNotifications.length) {
      navigate(`/GroupSpeakerInvitation/${groupSpeakerNotifications[newIndex].id}`);
    }
  };

  const handleResponse = (response: "accept" | "reject") => {
    if (!notification) return;
    
    // Access data with proper type
    const data = notification.notification_data as GroupSpeakerInvitationNotificationData;
    
    dispatch(
      sendWebSocketMessage("Group_Speaker_Invitation", response, {
        invitation_id: data.invitation_id,
        response
      })
    );

    dispatch(removeNotification(notification.id));

    if (groupSpeakerNotifications.length > 1) {
      const nextIndex = currentIndex < groupSpeakerNotifications.length - 1 
        ? currentIndex 
        : currentIndex - 1;
      navigate(`/GroupSpeakerInvitation/${groupSpeakerNotifications[nextIndex].notification_number}`);
    } else {
      navigate('/home');
    }
  };

  if (!notification) {
    return <div className="group-speaker-invitation-container">Notification not found</div>;
  }

  // Cast to specific type for safe destructuring
  const data = notification.notification_data as GroupSpeakerInvitationNotificationData;
  const { group_name, profile_picture, founder_name, action_required, status } = data;

  return (
    <div className="group-speaker-invitation-container">
      <div className="group-speaker-invitation-card">
        <div className="group-speaker-invitation-content">
          <ProfileImage
            imageUrl={profile_picture || "/default-group.png"}
            name={group_name}
          />
          <div className="group-speaker-invitation-name">{group_name}</div>
          <div className="group-speaker-invitation-message">
            {notification.notification_message}
          </div>
          <div className="group-speaker-invitation-founder">
            Invited by: {founder_name}
          </div>
          <div className={`group-speaker-invitation-status ${status.toLowerCase()}`}>
            Status: {status}
          </div>
        </div>

        {action_required ? (
          <div className="group-speaker-invitation-actions">
            <button 
              className="group-speaker-invitation-action accept" 
              onClick={() => handleResponse("accept")}
            >
              Accept
            </button>
            <p className="group-speaker-invitation-separator">|</p>
            <button 
              className="group-speaker-invitation-action reject"
              onClick={() => handleResponse("reject")}
            >
              Reject
            </button>
          </div>
        ) : (
          <div className="group-speaker-invitation-status-message">
            You've already responded to this invitation
          </div>
        )}
      </div>

      <div className="group-speaker-invitation-navigation">
        <button
          className='group-speaker-invitation-nav-button'
          onClick={() => handleNavigation('prev')}
          disabled={currentIndex <= 0}
        >
          Back
        </button>
        <button
          className='group-speaker-invitation-nav-button'
          onClick={() => handleNavigation('next')}
          disabled={currentIndex >= groupSpeakerNotifications.length - 1}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default GroupSpeakerInvitation;