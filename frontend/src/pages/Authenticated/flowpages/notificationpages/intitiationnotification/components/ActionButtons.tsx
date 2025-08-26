// import React from 'react';
// import '../styles.css';
// import { useDispatch, useSelector } from 'react-redux';
// import { removeNotification } from '../../notification_state/notificationsSlice';
// import { sendWebSocketMessage } from '../../notification_state/notificationsThunk';
// import { AppDispatch, RootState } from '../../../../../../store';
// import { useNavigate } from 'react-router-dom';

// interface ActionButtonsProps {
//   notificationId: string;
//   notificationNumber: string;
//   gmail: string;
// }

// const ActionButtons: React.FC<ActionButtonsProps> = ({ notificationId, notificationNumber, gmail }) => {
//   const dispatch: AppDispatch = useDispatch();
//   const navigate = useNavigate();
//   const notifications = useSelector((state: RootState) => state.notifications.notifications);

//   const handleAction = (response: "yes" | "no") => {
//     dispatch(sendWebSocketMessage("Initiation_Notification","verify_user", { 
//       notificationId: notificationNumber,
//       gmail,
//       response 
//     }));

//     dispatch(removeNotification(Number(notificationId)));

//     // Find the current index
//     const currentIndex = notifications.findIndex(n => n.notification_number === notificationNumber);
    
//     // Determine next notification or navigate home
//     if (notifications.length > 1) {
//       const nextIndex = currentIndex + 1 < notifications.length ? currentIndex + 1 : currentIndex - 1;
//       const nextNotification = notifications[nextIndex];

//       if (nextNotification) {
//         navigate(`/notifications/${nextNotification.notification_number}`);
//       }
//     } else {
//       navigate('/home'); // Redirect if no more notifications
//     }
//   };

//   return (
//     <div className="action-buttons" role="group" aria-label="Profile actions">
//       <button 
//         className="action-button" 
//         onClick={() => handleAction("yes")} 
//         aria-label="Accept profile"
//       >
//         <p className="action-button-text">Accept</p>
//       </button>
//       <p className="separator-text">{" | "}</p>
//       <button 
//         className="action-button" 
//         onClick={() => handleAction("no")} 
//         aria-label="Reject profile"
//       >
//         <p className="action-button-text">Reject</p>
//       </button>
//     </div>
//   );
// };

// export default ActionButtons;

// import React from 'react';
// import '../styles.css';
// import { useDispatch, useSelector } from 'react-redux';
// import { removeNotification } from '../../notification_state/notificationsSlice';
// import { AppDispatch, RootState } from '../../../../../../store';
// import { useNavigate } from 'react-router-dom';
// import api from '../../../../../../api'; // Import your API instance

// interface ActionButtonsProps {
//   notificationId: string;
//   notificationNumber: string;
//   gmail: string;
// }

// const ActionButtons: React.FC<ActionButtonsProps> = ({ notificationId, notificationNumber, gmail }) => {
//   const dispatch: AppDispatch = useDispatch();
//   const navigate = useNavigate();
//   const notifications = useSelector((state: RootState) => state.notifications.notifications);

//   const handleAction = async (response: "yes" | "no") => {
//     try {
//       // Make API call instead of WebSocket
//       const apiResponse = await api.post('/api/pendingusers/successful-experience/verify-response/', {
//         notificationId: notificationNumber,
//         response: response,
//         gmail: gmail
//       });

//       console.log('API Response:', apiResponse.data);

//       // Remove notification from UI
//       dispatch(removeNotification(Number(notificationId)));

//       // If response is "yes" and we have user data, navigate to blog creator
//       const data = apiResponse.data as { user?: any };
//       if (response === "yes" && data.user) {
        
//         const insightData={
//           type: "successful_experience",
//           target_user: data.user.id,
//           name: data.user.name,
//           profile_picture: data.user.profile_picture,
//         }
//         navigate('/blog-creator', {
//           state: { insightData}
//         }
        
        
//       );
//       dispatch(removeNotification(Number(notificationId)));
//       } else {
//         // For "no" response or if no user data, navigate home
//         navigate('/home');
//         dispatch(removeNotification(Number(notificationId)));
//       }
//     } catch (error) {
//       console.error('Verification failed:', error);
//       // Handle error (show message to user, etc.)
//     }
//   };

//   return (
//     <div className="action-buttons" role="group" aria-label="Profile actions">
//       <button 
//         className="action-button" 
//         onClick={() => handleAction("yes")} 
//         aria-label="Accept profile"
//       >
//         <p className="action-button-text">Accept</p>
//       </button>
//       <p className="separator-text">{" | "}</p>
//       <button 
//         className="action-button" 
//         onClick={() => handleAction("no")} 
//         aria-label="Reject profile"
//       >
//         <p className="action-button-text">Reject</p>
//       </button>
//     </div>
//   );
// };

// export default ActionButtons;


// ActionButtons.tsx


import React from 'react';
import '../styles.css';
import { useDispatch, useSelector } from 'react-redux';
import { removeNotification } from '../../notification_state/notificationsSlice';
import { AppDispatch, RootState } from '../../../../../../store';
import { useNavigate } from 'react-router-dom';
import api from '../../../../../../api';

interface ActionButtonsProps {
  notificationId: string;
  notificationNumber: string;
  gmail: string;
}

const ActionButtons: React.FC<ActionButtonsProps> = ({ notificationId, notificationNumber, gmail }) => {
  const dispatch: AppDispatch = useDispatch();
  const navigate = useNavigate();

  const handleAction = async (response: "yes" | "no") => {
    try {
      // Make API call instead of WebSocket
      const apiResponse = await api.post('/api/pendingusers/successful-experience/verify-response/', {
        notificationId: notificationNumber,
        response: response,
        gmail: gmail
      });

      console.log('API Response:', apiResponse.data);

      // Remove notification from UI
      dispatch(removeNotification(Number(notificationId)));

      // If response is "yes" and we have user data, navigate to blog creator
      const data = apiResponse.data as { user?: any };
      if (response === "yes" && data.user) {
        // Create the correct insightData structure
        const insightData = {
          type: "successful_experience",
          target_user: data.user.id,
          name: data.user.name,
          profile_picture: data.user.profile_picture,
        };
        
        // Navigate with the correct structure
        navigate('/blog-creator', { state: insightData });
      } else {
        // For "no" response or if no user data, navigate home
        navigate('/home');
      }
    } catch (error) {
      console.error('Verification failed:', error);
      // Handle error (show message to user, etc.)
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