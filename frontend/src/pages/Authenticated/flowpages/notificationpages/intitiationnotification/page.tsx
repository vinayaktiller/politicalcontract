import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import './styles.css';
import ProfileImage from './components/ProfileImage';
import AddressDetails from './components/AddressDetails';
import ActionButtons from './components/ActionButtons';

import { sendWebSocketMessage } from '../notification_state/notificationsThunk';
import { AppDispatch, RootState } from '../../../../../store';
import { markAsViewed } from '../notification_state/notificationsSlice';
import { Notification, InitiationNotificationData } from '../notification_state/notificationsTypes';

const InitiationNotification: React.FC = () => {
    const { notificationNumber } = useParams<{ notificationNumber: string }>();
    const navigate = useNavigate();
    const dispatch: AppDispatch = useDispatch();

    // Get the correct notifications
    const notifications = useSelector((state: RootState) =>
        state.notifications.notifications.filter(n =>
            n.notification_type === "Initiation_Notification"
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
                sendWebSocketMessage("Initiation_Notification", "update_seen_status", {
                    notificationId: notification.notification_number,
                    seen: true
                })
            );
        }
    }, [dispatch, notification]);

    useEffect(() => {
        const handleResize = () => {
            const profileContainer = document.querySelector('.profile-container');
            if (profileContainer) {
                profileContainer.classList.toggle('center-profile', window.innerHeight > 800);
            }
        };

        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleNavigation = (direction: 'prev' | 'next') => {
        const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex >= 0 && newIndex < notifications.length) {
            const newNotification = notifications[newIndex];
            navigate(`/notifications/${newNotification.notification_number}`);
        }
    };

    if (!notification) {
        return <div className="profile-container">Notification not found</div>;
    }

    const notificationData = notification.notification_data;

    // **Type Guard to Verify Notification Data**
    const isInitiationNotification = (data: any): data is InitiationNotificationData => {
        return 'first_name' in data && 'last_name' in data && 'profile_picture' in data;
    };

    return (
        <div className="profile-container">
            <div className="profile-card">
                <div className="profile-content">
                    <ProfileImage
                        imageUrl={isInitiationNotification(notificationData) ? notificationData.profile_picture || "default-profile.png" : "default-profile.png"}
                        name={isInitiationNotification(notificationData) ? `${notificationData.first_name} ${notificationData.last_name}` : "Unknown Applicant"}
                    />
                    <div className="profile-name">
                        {isInitiationNotification(notificationData) ? `${notificationData.first_name} ${notificationData.last_name}` : "Unknown"}
                    </div>
                    <div className="profile-dob">
                        Date of birth <br />
                        {isInitiationNotification(notificationData) ? new Date(notificationData.date_of_birth).toLocaleDateString() : "Unknown"}
                    </div>
                    <div className="profile-gender">
                        Gender: {isInitiationNotification(notificationData) ? notificationData.gender : "Unknown"}
                    </div>
                    {isInitiationNotification(notificationData) && (
                        <AddressDetails
                            country={notificationData.country}
                            state={notificationData.state}
                            district={notificationData.district}
                            subdistrict={notificationData.subdistrict}
                            village={notificationData.village}
                        />
                    )}
                </div>
                <ActionButtons
                    notificationId={String(notification.id)}
                    notificationNumber={notification.notification_number}
                    gmail={isInitiationNotification(notificationData) ? notificationData.gmail : "Unknown"}
                />
            </div>
            <div className="navigation-buttons">
                <button
                    className='navigation-button'
                    onClick={() => handleNavigation('prev')}
                    disabled={currentIndex <= 0}
                >
                    Back
                </button>
                <button
                    className='navigation-button'
                    onClick={() => handleNavigation('next')}
                    disabled={currentIndex >= notifications.length - 1}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default InitiationNotification;


// UserProfile.tsx
//  import { sendWebSocketMessage } from '../notification_state/notificationsThunk';
//  import { AppDispatch, RootState } from '../../../../../store';
//  import { markAsViewed } from '../notification_state/notificationsSlice';
// // import { Notification } from '../notification_state/notificationsTypes';

// import React, { useEffect } from 'react';
// import { useParams, useNavigate } from 'react-router-dom';
// import { useSelector, useDispatch } from 'react-redux';
// //import { AppDispatch, RootState } from '../../store';
// //import { sendWebSocketMessage } from '../notificationsThunk';
// //import { markAsViewed } from '../notificationsSlice';
// import { NotificationDetails } from './components/NotificationDetails';
// import './styles.css';

// const UserProfile: React.FC = () => {
//   const { notificationNumber } = useParams<{ notificationNumber: string }>();
//   const navigate = useNavigate();
//   const dispatch = useDispatch<AppDispatch>();
//   const notifications = useSelector((state: RootState) => state.notifications.notifications);
  
//   const notification = notifications.find(n => n.notification_number === Number(notificationNumber));
//   const currentIndex = notifications.findIndex(n => n.notification_number === Number(notificationNumber));

//   useEffect(() => {
//     if (notification && !notification.notification_freshness) {
//       dispatch(markAsViewed(notification.id));
//       dispatch(
//         sendWebSocketMessage(notification.notification_type, "update_seen_status", { 
//           notificationId: notification.notification_number, 
//           seen: true 
//         })
//       );
//     }
//   }, [dispatch, notification]);

//   const handleNavigation = (direction: 'prev' | 'next') => {
//     const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
//     if (newIndex >= 0 && newIndex < notifications.length) {
//       const newNotification = notifications[newIndex];
//       navigate(`/notifications/${newNotification.notification_number}`);
//     }
//   };

//   if (!notification) {
//     return <div className="profile-container">Notification not found</div>;
//   }

//   return (
//     <div className="profile-container">
//       <NotificationDetails notification={notification} />
//       <div className="navigation-buttons">
//         <button 
//           className='navigation-button' 
//           onClick={() => handleNavigation('prev')} 
//           disabled={currentIndex <= 0}
//         >
//           Back
//         </button>
//         <button 
//           className='navigation-button' 
//           onClick={() => handleNavigation('next')} 
//           disabled={currentIndex >= notifications.length - 1}
//         >
//           Next
//         </button>
//       </div>
//     </div>
//   );
// };

// export default UserProfile;