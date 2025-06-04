import { useEffect } from 'react';
import { useDispatch } from "react-redux";
import { AppDispatch } from './store';
import { connectWebSocket, disconnectWebSocket } from './pages/Authenticated/flowpages/notificationpages/notification_state/notificationsThunk';
import AppRoutes from './AppRoutes';

const App = () => {
  const dispatch = useDispatch<AppDispatch>();

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
    <div>
      <AppRoutes />
    </div>  
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
