
import '../css/NotificationBar.css';
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { RootState, AppDispatch } from "../../store";
import { Notification } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsTypes";
import { triggerCelebration } from "../../pages/Authenticated/milestone/celebration/celebrationSlice";
import { removeNotificationByDetails } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsSlice";
import {addMilestone} from "../../pages/Authenticated/milestone/milestonesSlice";

interface NotificationBarProps {
  toggleNotifications: () => void;
}

const NotificationBar: React.FC<NotificationBarProps> = ({ toggleNotifications }) => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { notifications, isConnected } = useSelector((state: RootState) => state.notifications);

  // Add route for Group Speaker Invitation
  const notificationRoutes: Record<string, string> = {
    Initiation_Notification: "/Initiationnotifications",
    Connection_Notification: "/Connectionnotifications",
    Connection_Status: "/ConnectionStatusNotifications",
    Group_Speaker_Invitation: "/GroupSpeakerInvitation",
    Milestone_Notification: "/MilestoneNotifications"
  };

  const handleView = (notificationNumber: string) => {
    const notification = notifications.find(n => n.notification_number === notificationNumber);
    if (notification) {
      // Special handling for Milestone notifications
      if (notification.notification_type === "Milestone_Notification") {
        console.log('Handling Milestone Notification:', notification);
        const milestoneData = notification.notification_data;
        console.log('Milestone Data:', milestoneData);
        dispatch(addMilestone(milestoneData));


        // Trigger celebration modal
        dispatch(triggerCelebration({
          ...notification.notification_data,
          id: notification.id
        }));

        // Remove notification after triggering celebration
        dispatch(removeNotificationByDetails({
          notification_type: notification.notification_type,
          notification_number: notification.notification_number,
        }));
      } else {
      const routeBase = notificationRoutes[notification.notification_type];
      const destination = routeBase 
        ? `${routeBase}/${notification.id}`
        : `/notifications/${notification.id}`;
      navigate(destination);
    }
    toggleNotifications();
  }
};
  const classifyNotifications = (notificationGroup: Notification[]) => {
    return notificationGroup.reduce((acc, notification) => {
      const type = notification.notification_type;
      if (type && notificationRoutes[type]) {
        acc[type] = [...(acc[type] || []), notification];
      }
      return acc;
    }, {} as Record<string, Notification[]>);
  };

  const newNotifications = notifications.filter(n => !n.notification_freshness);
  console.log('New Notifications:', newNotifications);
  console.log('Old Notifications:', notifications.filter(n => n.notification_freshness));
  const oldNotifications = notifications.filter(n => n.notification_freshness);
  const groupedNewNotifications = classifyNotifications(newNotifications);
  const groupedOldNotifications = classifyNotifications(oldNotifications);

  return (
    <div className="notification-container">
      <div className="notification-header">
        <h3>Notifications {!isConnected && <span className="connecting-dot">●</span>}</h3>
      </div>

      {notifications.length === 0 ? (
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
                    key={notification.notification_number} 
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
                    key={notification.notification_number} 
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
