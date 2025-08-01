import React from 'react';
import '../styles.css';
import { useDispatch, useSelector } from 'react-redux';
import { removeNotification } from '../../notification_state/notificationsSlice';
import { sendWebSocketMessage } from '../../notification_state/notificationsThunk';
import { AppDispatch, RootState } from '../../../../../../store';
import { useNavigate } from 'react-router-dom';

interface ActionButtonsProps {
  notificationId: string;
  notificationNumber: number;
  gmail: string;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({ notificationId, notificationNumber, gmail }) => {
  const dispatch: AppDispatch = useDispatch();
  const navigate = useNavigate();
  const notifications = useSelector((state: RootState) => state.notifications.notifications);

  const handleAction = (response: "yes" | "no") => {
    dispatch(sendWebSocketMessage("Initiation_Notification","verify_user", { 
      notificationId: notificationNumber,
      gmail,
      response 
    }));

    dispatch(removeNotification(Number(notificationId)));

    // Find the current index
    const currentIndex = notifications.findIndex(n => n.notification_number === notificationNumber);
    
    // Determine next notification or navigate home
    if (notifications.length > 1) {
      const nextIndex = currentIndex + 1 < notifications.length ? currentIndex + 1 : currentIndex - 1;
      const nextNotification = notifications[nextIndex];

      if (nextNotification) {
        navigate(`/notifications/${nextNotification.notification_number}`);
      }
    } else {
      navigate('/home'); // Redirect if no more notifications
    }
  };

  return (
    <div className="action-buttons" role="group" aria-label="Profile actions">
      <button 
        className="action-button" 
        onClick={() => handleAction("yes")} 
        aria-label="Accept profile"
      >
        <p className="action-button-text">Accept</p>
      </button>
      <p className="separator-text">{" | "}</p>
      <button 
        className="action-button" 
        onClick={() => handleAction("no")} 
        aria-label="Reject profile"
      >
        <p className="action-button-text">Reject</p>
      </button>
    </div>
  );
};

export default ActionButtons;
