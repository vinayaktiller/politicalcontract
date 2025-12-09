import '../css/NotificationBar.css';
import React, { useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { RootState, AppDispatch } from "../../store";
import { Notification } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsTypes";
import { triggerCelebration } from "../../pages/Authenticated/milestone/celebration/celebrationSlice";
import { removeNotificationByDetails } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsSlice";
import { addMilestone } from "../../pages/Authenticated/milestone/milestonesSlice";
import api from "../../api";

interface NotificationBarProps {
  toggleNotifications: () => void;
}

const NotificationBar: React.FC<NotificationBarProps> = ({ toggleNotifications }) => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { notifications, isConnected } = useSelector((state: RootState) => state.notifications);

  const notificationRoutes: Record<string, string> = {
    Initiation_Notification: "/Initiationnotifications",
    Connection_Notification: "/Connectionnotifications",
    Connection_Status: "/ConnectionStatusNotifications",
    Group_Speaker_Invitation: "/GroupSpeakerInvitation",
    Milestone_Notification: "/MilestoneNotifications",
    Message_Notification: "/chat"
  };

  const handleView = useCallback(async (notificationNumber: string) => {
    const notification = notifications.find(n => n.notification_number === notificationNumber);
    if (!notification) return;

    // Special handling for Milestone notifications
    if (notification.notification_type === "Milestone_Notification") {
      const milestoneData = notification.notification_data;
      
      // Add milestone to Redux store first
      dispatch(addMilestone({
        ...milestoneData,
        // Ensure all required fields are present
        id: milestoneData.id || notification.id,
        milestone_id: milestoneData.milestone_id || `milestone_${Date.now()}`,
        title: milestoneData.title || "Milestone Achieved",
        text: milestoneData.text || "Congratulations on your achievement!",
        created_at: milestoneData.created_at || new Date().toISOString(),
        delivered: milestoneData.delivered || false,
        photo_id: milestoneData.photo_id || null,
        photo_url: milestoneData.photo_url || null,
        type: milestoneData.type || "initiation"
      }));

      // Trigger celebration modal with guaranteed data
      // Trigger celebration modal with guaranteed data
      dispatch(triggerCelebration({
        ...milestoneData,
        id: notification.id, // Use notification ID for tracking
        // Ensure celebration data has all required fields
        milestone_id: milestoneData.milestone_id,
        user_id: milestoneData.user_id,
        title: milestoneData.title,
        text: milestoneData.text,
        created_at: milestoneData.created_at,
        delivered: milestoneData.delivered,
        photo_id: milestoneData.photo_id,
        photo_url: milestoneData.photo_url,
        type: milestoneData.type
      }));
      // Call backend API to mark milestone as completed
      try {
        if (milestoneData.milestone_id) {
          await api.post('/api/users/milestones/complete/', {
            milestone_id: milestoneData.milestone_id
          });
          console.log('Milestone marked as completed successfully');
        }
      } catch (error) {
        console.error('Error calling milestone completion API:', error);
      }

      // Remove notification after triggering celebration
      setTimeout(() => {
        dispatch(removeNotificationByDetails({
          notification_type: notification.notification_type,
          notification_number: notification.notification_number,
        }));
      }, 100);
    } 
    // Handling for Message notifications
    else if (notification.notification_type === "Message_Notification") {
      navigate('/messages/chatlist');
      
      dispatch(removeNotificationByDetails({
        notification_type: notification.notification_type,
        notification_number: notification.notification_number,
      }));
    } 
    else {
      const routeBase = notificationRoutes[notification.notification_type];
      const destination = routeBase 
        ? `${routeBase}/${notification.id}`
        : `/notifications/${notification.id}`;
      navigate(destination);
    }
    
    toggleNotifications();
  }, [dispatch, navigate, notifications, toggleNotifications]);

  // Sort notifications by date (newest first)
  const sortedNotifications = [...notifications].sort((a, b) => {
    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
    return dateB - dateA;
  });

  const classifyNotifications = (notificationGroup: Notification[]) => {
    return notificationGroup.reduce((acc, notification) => {
      const type = notification.notification_type;
      if (type && notificationRoutes[type]) {
        acc[type] = [...(acc[type] || []), notification];
      }
      return acc;
    }, {} as Record<string, Notification[]>);
  };

  const newNotifications = sortedNotifications.filter(n => !n.notification_freshness);
  const oldNotifications = sortedNotifications.filter(n => n.notification_freshness);
  const groupedNewNotifications = classifyNotifications(newNotifications);
  const groupedOldNotifications = classifyNotifications(oldNotifications);

  return (
    <div className="notification-container">
      <div className="notification-header">
        <h3>Notifications {!isConnected && <span className="connecting-dot">●</span>}</h3>
      </div>

      {sortedNotifications.length === 0 ? (
        <div className="empty-state">
          <p>No notifications available</p>
        </div>
      ) : (
        <div className="notification-lists">
          {Object.entries(groupedNewNotifications).map(([type, notifications]) => (
            <div key={type} className={`notification-group ${type.toLowerCase().replace(/_/g, '-')}-new`}>
              <h4>New {type.replace(/_/g, ' ')}</h4>
              <ul>
                {notifications.map(notification => (
                  <li 
                    key={`${notification.notification_number}-${notification.id}`}
                    className="notification-item unread"
                    onClick={() => handleView(notification.notification_number)}
                  >
                    <div className="notification-content">
                      <p className="message">{notification.notification_message}</p>
                      <div className="meta">
                        <span className="type">{type.replace(/_/g, ' ')}</span>
                        {notification.created_at && (
                          <span className="time">
                            {new Date(notification.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {Object.entries(groupedOldNotifications).map(([type, notifications]) => (
            <div key={type} className={`notification-group ${type.toLowerCase().replace(/_/g, '-')}-old`}>
              <h4>Previous {type.replace(/_/g, ' ')}</h4>
              <ul>
                {notifications.map(notification => (
                  <li 
                    key={`${notification.notification_number}-${notification.id}`}
                    className="notification-item read"
                    onClick={() => handleView(notification.notification_number)}
                  >
                    <div className="notification-content">
                      <p className="message">{notification.notification_message}</p>
                      <div className="meta">
                        <span className="type">{type.replace(/_/g, ' ')}</span>
                        {notification.created_at && (
                          <span className="time">
                            {new Date(notification.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationBar;