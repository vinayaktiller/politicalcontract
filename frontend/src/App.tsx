import React, { useEffect, useRef } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from './store';
import { connectWebSocket, disconnectWebSocket } from './pages/Authenticated/flowpages/notificationpages/notification_state/notificationsThunk';
import AppRoutes from './AppRoutes';
import CelebrationModal from './pages/Authenticated/milestone/celebration/CelebrationModal';

const INACTIVITY_LIMIT = 2 * 60 * 1000; // 2 minutes

const App: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const celebration = useSelector((state: RootState) => state.celebration);

  const activityTimeout = useRef<NodeJS.Timeout | null>(null);
  const wsActive = useRef(false); // Track websocket connection

  // Debug log celebration state changes (optional)
  useEffect(() => {
    console.log('Celebration state changed:', celebration.isOpen, celebration.data);
  }, [celebration.isOpen, celebration.data]);

  // Disconnect after 2 min inactivity, reconnect if user interacts or returns
  useEffect(() => {
    const userId = localStorage.getItem("user_id");

    // Handler to reset timeout and reconnect if needed
    const onUserActivity = () => {
      // If websocket is disconnected, reconnect on activity
      if (userId && !wsActive.current) {
        dispatch(connectWebSocket(userId));
        wsActive.current = true;
      }
      if (activityTimeout.current) clearTimeout(activityTimeout.current);
      activityTimeout.current = setTimeout(() => {
        dispatch(disconnectWebSocket());
        wsActive.current = false;
      }, INACTIVITY_LIMIT);
    };

    // Handler for app visibility changes
    const onVisibilityChange = () => {
      if (document.visibilityState !== "visible") {
        dispatch(disconnectWebSocket());
        wsActive.current = false;
        if (activityTimeout.current) clearTimeout(activityTimeout.current);
      } else {
        onUserActivity(); // Reconnect when tab becomes active
      }
    };

    if (userId) {
      dispatch(connectWebSocket(userId));
      wsActive.current = true;
      activityTimeout.current = setTimeout(() => {
        dispatch(disconnectWebSocket());
        wsActive.current = false;
      }, INACTIVITY_LIMIT);

      // Listen for user events
      window.addEventListener('mousemove', onUserActivity);
      window.addEventListener('keydown', onUserActivity);
      window.addEventListener('touchstart', onUserActivity);
      window.addEventListener('mousedown', onUserActivity);

      // Listen for window/tab visibility change
      document.addEventListener('visibilitychange', onVisibilityChange);
    }

    return () => {
      dispatch(disconnectWebSocket());
      wsActive.current = false;
      if (activityTimeout.current) clearTimeout(activityTimeout.current);
      window.removeEventListener('mousemove', onUserActivity);
      window.removeEventListener('keydown', onUserActivity);
      window.removeEventListener('touchstart', onUserActivity);
      window.removeEventListener('mousedown', onUserActivity);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [dispatch]);

  return (
    <BrowserRouter>
      <div className="app-container">
        <AppRoutes />
        {celebration.isOpen && celebration.data && (
          <CelebrationModal data={celebration.data} />
        )}
      </div>
    </BrowserRouter>
  );
};

export default App;




// import { useEffect } from 'react';
// import { useDispatch } from "react-redux";
// import { AppDispatch } from './store';
// import AppRoutes from './AppRoutes';

// const App = () => {
//   const dispatch = useDispatch<AppDispatch>();

//   useEffect(() => {
//     const userId = localStorage.getItem("user_id");
//     if (userId) {
//       console.log("User ID found:", userId);
//       // WebSocket-related logic removed
//     }

//     return () => {
//       console.log("Cleanup function called");
//       // WebSocket-related cleanup removed
//     };
//   }, [dispatch]);

//   return (
//     <div>
//       <AppRoutes />
//     </div>  
//   );
// };

// export default App;
