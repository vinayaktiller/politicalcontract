// src/App.tsx
import React, { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from './store';
import { connectWebSocket, disconnectWebSocket } from './pages/Authenticated/flowpages/notificationpages/notification_state/notificationsThunk';
import AppRoutes from './AppRoutes';
import CelebrationModal from './pages/Authenticated/milestone/celebration/CelebrationModal';

const App: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const celebration = useSelector((state: RootState) => state.celebration);

  // Debug log celebration state changes (optional)
  useEffect(() => {
    console.log('Celebration state changed:', celebration.isOpen, celebration.data);
  }, [celebration.isOpen, celebration.data]);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (userId) {
      dispatch(connectWebSocket(userId));
    }

    return () => {
      dispatch(disconnectWebSocket());
    };
  }, [dispatch]);

  return (
    <BrowserRouter> {/* Wrap entire app with BrowserRouter */}
      <div className="app-container">
        {/* Your routes component goes here */}
        <AppRoutes />

        {/* Only show CelebrationModal if open and has valid data */}
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
