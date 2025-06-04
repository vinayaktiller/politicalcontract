import React from 'react';
import '../styles.css';
import { useDispatch, useSelector } from 'react-redux';
import { removeNotification } from '../../notification_state/notificationsSlice';
import { sendWebSocketMessage } from '../../notification_state/notificationsThunk';
import { AppDispatch, RootState } from '../../../../../../store';
import { useNavigate } from 'react-router-dom';

interface ConnectionActionButtonsProps {
  notificationId: string;
  notificationNumber: number;
  connectionId: number;
  initiatorId: number;
}

const ConnectionActionButtons: React.FC<ConnectionActionButtonsProps> = ({ 
  notificationId, 
  notificationNumber,
  connectionId,
  initiatorId
}) => {
  const dispatch: AppDispatch = useDispatch();
  const navigate = useNavigate();
  const notifications = useSelector((state: RootState) => state.notifications.notifications);

  const handleConnectionAction = (action: "accept" | "reject") => {
    dispatch(sendWebSocketMessage("Connection_Notification", "connection_action", {
      connectionId,
      initiatorId,
      action,
      notificationNumber
    }));

    dispatch(removeNotification(Number(notificationId)));

    const currentIndex = notifications.findIndex(n => 
      n.notification_number === notificationNumber &&
      n.notification_type === "Connection_Notification"
    );

    if (notifications.length > 1) {
      const connectionNotifications = notifications.filter(n => 
        n.notification_type === "Connection_Notification"
      );
      const nextIndex = currentIndex + 1 < connectionNotifications.length ? currentIndex + 1 : currentIndex - 1;
      const nextNotification = connectionNotifications[nextIndex];

      if (nextNotification) {
        navigate(`/notifications/${nextNotification.notification_number}`);
      }
    } else {
      navigate('/home');
    }
  };

  return (
    <div className="conn-action-buttons" role="group" aria-label="Connection actions">
      <button 
        className="conn-action-button accept" 
        onClick={() => handleConnectionAction("accept")}
      >
        Confirm Connection
      </button>
      <button 
        className="conn-action-button reject" 
        onClick={() => handleConnectionAction("reject")}
      >
        Remove Connection
      </button>
    </div>
  );
};

export default ConnectionActionButtons;