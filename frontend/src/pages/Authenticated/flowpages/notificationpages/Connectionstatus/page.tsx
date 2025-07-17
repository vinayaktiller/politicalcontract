import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import './styles.css';
import { sendWebSocketMessage } from '../notification_state/notificationsThunk';
import { AppDispatch, RootState } from '../../../../../store';
import { markAsViewed, removeNotification } from '../notification_state/notificationsSlice';
import { Notification, ConnectionStatusNotificationData } from '../notification_state/notificationsTypes';

const isConnectionStatusNotification = (data: any): data is ConnectionStatusNotificationData => {
    return 'applicant_name' in data && 'status' in data && 'status_message' in data;
};

const ConnectionStatusNotification: React.FC = () => {
    const { notificationNumber } = useParams<{ notificationNumber: string }>();
    const navigate = useNavigate();
    const dispatch: AppDispatch = useDispatch();
    const [isProcessing, setIsProcessing] = useState(false);

    const notifications = useSelector((state: RootState) =>
        state.notifications.notifications.filter(n =>
            n.notification_type === "Connection_Status"
        )
    );

    const notification = notifications.find(n =>
        n.notification_number === Number(notificationNumber)
    );

    const currentIndex = notifications.findIndex(n =>
        n.notification_number === Number(notificationNumber)
    );

    useEffect(() => {
        if (notification && !notification.notification_freshness) {
            dispatch(markAsViewed(notification.id));
        }
    }, [dispatch, notification]);

    const handleNavigation = (direction: 'prev' | 'next') => {
        const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex >= 0 && newIndex < notifications.length) {
            navigate(`/ConnectionStatusNotifications/${notifications[newIndex].notification_number}`);
        }
    };

    const handleAction = (actionType: 'drop' | 'acknowledge') => {
        if (!notification || !isConnectionStatusNotification(notification.notification_data)) return;
        
        setIsProcessing(true);
        const notificationData = notification.notification_data as ConnectionStatusNotificationData;
        
        dispatch(
            sendWebSocketMessage("Connection_Status", actionType, {
                notificationId: notification.notification_number,
                connectionId: notificationData.connection_id
            })
        );
        setIsProcessing(false);
        dispatch(removeNotification(notification.id));
        navigate('/home');
    };

    if (!notification) {
        return <div className="cs-notification-container">Connection status notification not found</div>;
    }

    const notificationData = notification.notification_data;

    return (
        <div className="cs-notification-container">
            <div className="cs-notification-card">
                <div className="cs-profile-container">
                    <img 
                        src={notificationData.profile_picture || "default-profile.png"} 
                        alt={isConnectionStatusNotification(notificationData) ? `${notificationData.applicant_name}'s profile` : "Unknown Applicant"} 
                        className="cs-profile-image"
                        onError={(e) => e.currentTarget.src = "default-profile.png"} 
                    />
                    <p className="cs-profile-name">{isConnectionStatusNotification(notificationData) ? notificationData.applicant_name : "Unknown Applicant"}</p>
                </div>

                <div className="cs-message-container">
                    <p className="cs-message">
                        {isConnectionStatusNotification(notificationData) ? notificationData.status_message : "No status message available"}
                    </p>
                </div>

                <p className="cs-status-label">
                    <strong>Status:</strong> {isConnectionStatusNotification(notificationData) ? notificationData.status : "Unknown"}
                </p>
                
                {/* Action Buttons */}
                {isConnectionStatusNotification(notificationData) && (
                    <div className="cs-action-buttons">
                        {['connection_offline', 'sent', 'not_viewed', 'reacted_pending'].includes(notificationData.status) && (
                            <button
                                className="cs-action-button cs-drop-button"
                                onClick={() => handleAction('drop')}
                                disabled={isProcessing}
                            >
                                {isProcessing ? 'Processing...' : 'Drop Connection'}
                            </button>
                        )}
                        
                        {['accepted', 'rejected'].includes(notificationData.status) && (
                            <button
                                className="cs-action-button cs-ok-button"
                                onClick={() => handleAction('acknowledge')}
                                disabled={isProcessing}
                            >
                                {isProcessing ? 'Processing...' : 'OK'}
                            </button>
                        )}
                    </div>
                )}
            </div>

            <div className="cs-navigation-buttons">
                <button
                    className='cs-nav-button cs-prev-button'
                    onClick={() => handleNavigation('prev')}
                    disabled={currentIndex <= 0}
                >
                    Back
                </button>
                <button
                    className='cs-nav-button cs-next-button'
                    onClick={() => handleNavigation('next')}
                    disabled={currentIndex >= notifications.length - 1}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default ConnectionStatusNotification;