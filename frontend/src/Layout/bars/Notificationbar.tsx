// import '../css/NotificationBar.css';
// // NotificationBar.tsx
// import React from "react";
// import { useDispatch, useSelector } from "react-redux";
// import { Link } from "react-router-dom";
// import { RootState, AppDispatch } from "../../store";
// import { sendWebSocketMessage } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsThunk";
// import { Notification } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsTypes";

// interface NotificationBarProps {
//   toggleNotifications: () => void;
// }

// const NotificationBar: React.FC<NotificationBarProps> = ({ toggleNotifications }) => {
//   const dispatch = useDispatch<AppDispatch>();
//   const { notifications, isConnected } = useSelector((state: RootState) => state.notifications);

//   const handleView = (notificationNumber: number) => {
//     const notification = notifications.find(n => n.notification_number === notificationNumber);
//     if (notification) {
//       dispatch(sendWebSocketMessage(notification.notification_type, "update_seen_status", {
//         notificationId: notificationNumber,
//         seen: true
//       }));
//     }
//     toggleNotifications();
//   };

//   const newNotifications = notifications.filter(n => !n.notification_freshness);
//   const oldNotifications = notifications.filter(n => n.notification_freshness);

//   return (
//     <div className="notification-container">
//       <div className="notification-header">
//         <h3>Notifications {!isConnected && <span className="connecting-dot">●</span>}</h3>
//       </div>

//       {notifications.length === 0 ? (
//         <div className="empty-state">
//           <p>No notifications available</p>
//         </div>
//       ) : (
//         <div className="notification-lists">
//           {newNotifications.length > 0 && (
//             <div className="notification-group new-notifications">
//               <h4>New</h4>
//               <ul>
//                 {newNotifications.map((notification) => (
//                   <li
//                     key={notification.notification_number}
//                     className="notification-item unread"
//                     onClick={() => handleView(notification.notification_number)}
//                   >
//                     <Link to={`/notifications/${notification.notification_number}`}>
//                       <div className="notification-content">
//                         <p className="message">{notification.notification_message}</p>
//                         <div className="meta">
//                           <span className="type">{notification.notification_type}</span>
//                           {notification.created_at && (
//                             <span className="time">
//                               {new Date(notification.created_at).toLocaleDateString()}
//                             </span>
//                           )}
//                         </div>
//                       </div>
//                     </Link>
//                   </li>
//                 ))}
//               </ul>
//             </div>
//           )}

//           {oldNotifications.length > 0 && (
//             <div className="notification-group old-notifications">
//               <h4>Previous</h4>
//               <ul>
//                 {oldNotifications.map((notification) => (
//                   <li
//                     key={notification.notification_number}
//                     className="notification-item read"
//                     onClick={toggleNotifications}
//                   >
//                     <Link to={`/notifications/${notification.notification_number}`}>
//                       <div className="notification-content">
//                         <p className="message">{notification.notification_message}</p>
//                         <div className="meta">
//                           <span className="type">{notification.notification_type}</span>
//                           {notification.created_at && (
//                             <span className="time">
//                               {new Date(notification.created_at).toLocaleDateString()}
//                             </span>
//                           )}
//                         </div>
//                       </div>
//                     </Link>
//                   </li>
//                 ))}
//               </ul>
//             </div>
//           )}
//         </div>
//       )}
//     </div>
//   );
// };

// export default NotificationBar;

import '../css/NotificationBar.css';
import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { RootState, AppDispatch } from "../../store";
import { sendWebSocketMessage } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsThunk";
import { Notification } from "../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsTypes";

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
    Group_Speaker_Invitation: "/GroupSpeakerInvitation"
  };

  const handleView = (notificationNumber: number) => {
    const notification = notifications.find(n => n.id === notificationNumber);
    if (notification) {
      const routeBase = notificationRoutes[notification.notification_type];
      const destination = routeBase 
        ? `${routeBase}/${notification.notification_number}`
        : `/notifications/${notificationNumber}`;
      navigate(destination);
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
                    onClick={() => handleView(notification.id)}
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
                    onClick={() => handleView(notification.id)}
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