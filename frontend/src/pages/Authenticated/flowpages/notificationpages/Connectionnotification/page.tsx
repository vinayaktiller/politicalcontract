import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import './styles.css';
import ProfileImage from './components/ProfileImage';
import AddressDetails from './components/AddressDetails';
import ConnectionActionButtons from './components/ActionButtons';
import { sendWebSocketMessage } from '../notification_state/notificationsThunk';
import { AppDispatch, RootState } from '../../../../../store';
import { markAsViewed } from '../notification_state/notificationsSlice';
import { Notification, ConnectionNotificationData } from '../notification_state/notificationsTypes';

const ConnectionNotification: React.FC = () => {
    const { notificationNumber } = useParams<{ notificationNumber: string }>();
    const navigate = useNavigate();
    const dispatch: AppDispatch = useDispatch();

    // Get the correct notifications
    const notifications = useSelector((state: RootState) =>
        state.notifications.notifications.filter(n =>
            n.notification_type === "Connection_Notification"
        )
    );

    console.log("Filtered Notifications:", notifications);

    const notification = notifications.find(n =>
        n.notification_number === Number(notificationNumber)
    );

    console.log("This Notification:", notification);

    const currentIndex = notifications.findIndex(n =>
        n.notification_number === Number(notificationNumber)
    );

    useEffect(() => {
        if (notification && !notification.notification_freshness) {
            dispatch(markAsViewed(notification.id));
            dispatch(
                sendWebSocketMessage("Connection_Notification", "update_seen_status", {
                    notificationId: notification.notification_number,
                    seen: true
                })
            );
        }
    }, [dispatch, notification]);

    const handleNavigation = (direction: 'prev' | 'next') => {
        const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex >= 0 && newIndex < notifications.length) {
            const newNotification = notifications[newIndex];
            navigate(`/Connectionnotifications/${newNotification.notification_number}`);
        }
    };

    if (!notification) {
        return <div className="conn-profile-container">Connection notification not found</div>;
    }

    const notificationData = notification.notification_data;

    // **Check if notificationData matches ConnectionNotificationData**
    const isConnectionNotification = (data: any): data is ConnectionNotificationData => {
        return 'first_name' in data && 'last_name' in data && 'profile_picture' in data;
    };

   return (
    <div className="conn-profile-container">
      <div className="conn-profile-card">
        <div className="conn-profile-content">
          <ProfileImage
            imageUrl={
              isConnectionNotification(notificationData)
                ? notificationData.profile_picture || "default-profile.png"
                : "default-profile.png"
            }
            name={
              isConnectionNotification(notificationData)
                ? `${notificationData.first_name} ${notificationData.last_name}`
                : "Unknown Applicant"
            }
          />
          <div className="conn-profile-name">
            {isConnectionNotification(notificationData)
              ? `${notificationData.first_name} ${notificationData.last_name}`
              : "Unknown"}
            {"id" in notificationData && (
              <span className="conn-profile-id">ID: {notificationData.id}</span>
            )}
          </div>
          <div className="conn-profile-dob">
            Date of birth <br />
            {isConnectionNotification(notificationData)
              ? new Date(notificationData.date_of_birth).toLocaleDateString()
              : "Unknown"}
          </div>
          <div className="conn-profile-gender">
            Gender:{" "}
            {isConnectionNotification(notificationData)
              ? notificationData.gender
              : "Unknown"}
          </div>
          {isConnectionNotification(notificationData) && (
            <AddressDetails
              country={notificationData.country}
              state={notificationData.state}
              district={notificationData.district}
              subdistrict={notificationData.subdistrict}
              village={notificationData.village}
            />
          )}
        </div>
        {"id" in notificationData && notificationData.id !== undefined && (
          <ConnectionActionButtons
            notificationId={String(notification.id)}
            notificationNumber={notification.notification_number}
            connectionId={notificationData.id}
            initiatorId={notificationData.initiator_id}
          />
        )}
      </div>
      <div className="conn-navigation-buttons">
        <button
          className="conn-navigation-button"
          onClick={() => handleNavigation("prev")}
          disabled={currentIndex <= 0}
        >
          Back
        </button>
        <button
          className="conn-navigation-button"
          onClick={() => handleNavigation("next")}
          disabled={currentIndex >= notifications.length - 1}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default ConnectionNotification;