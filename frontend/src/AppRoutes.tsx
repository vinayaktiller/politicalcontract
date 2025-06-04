// import React from "react";
// import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
// import { GoogleOAuthProvider } from "@react-oauth/google";

// import LoginPage from "./pages/Unauthenticated/Loginpage/LoginPage"
// import Registration from "./pages/Unauthenticated/Registration/Registration";
// import Waitingpage from "./pages/Unauthenticated/Waitingpage/Waitingpage";
// import Mainbar from "./Layout/bars/Mainbar";
// import HomePage from "./pages/Authenticated/homepage/HomePage";
// import ProtectedRoute from "./login/ProtectedRoute"; // Import the ProtectedRoute component
// import ConnexionVerification from "./pages/Authenticated/flowpages/Connectionrelatedpages/makeconnections/page";
// import ConnectionNotification from "./pages/Authenticated/flowpages/notificationpages/Connectionnotification/page";
// import InitiationNotification from "./pages/Authenticated/flowpages/notificationpages/intitiationnotification/page";

// const clientId = "719395873709-ese7vg45i9gfndador7q6rmq3untnkcr.apps.googleusercontent.com"; // Replace with your actual Google OAuth client ID

// const AppRoutes: React.FC = () => {
//   console.log("AppRoutes component is mounted!");

//   return (
//     <GoogleOAuthProvider clientId={clientId}>
//       <BrowserRouter>
//         <Routes>
//           <Route path="/login" element={<LoginPage />} />
//           <Route path="/register" element={<Registration />} />
//           <Route path="*" element={<Navigate to="/login" replace />} />
//           <Route path="/waiting" element={<Waitingpage />} />
//           <Route path="/" element={<ProtectedRoute />}>
//             <Route path="/" element={<Mainbar />}>

//               <Route path="home" element={<HomePage />} />
//               <Route path="Initiationnotifications/:notificationNumber" element={<InitiationNotification />} />
//               <Route path="Connectionnotifications/:notificationNumber" element={<ConnectionNotification />} />
              
              
//               <Route path="make-connections" element={<ConnexionVerification />} />
              
//               {/* Add more authenticated routes here */}
//               {/* Example: */}
//               {/* <Route path="profile" element={<UserProfile />} /> */}
//               {/* Add more routes here as needed */}
              
//               {/* Example of a nested route */}
//               {/* Add more authenticated routes here */}



//             </Route>
//           </Route>
           
//           {/* Add more routes here as needed */}
//         </Routes>
//       </BrowserRouter>
//     </GoogleOAuthProvider>
//   );
// };

// export default AppRoutes;

import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";

import LoginPage from "./pages/Unauthenticated/Loginpage/LoginPage";
import Registration from "./pages/Unauthenticated/Registration/Registration";
import Waitingpage from "./pages/Unauthenticated/Waitingpage/Waitingpage";
import Mainbar from "./Layout/bars/Mainbar";
import HomePage from "./pages/Authenticated/homepage/HomePage";
import ProtectedRoute from "./login/ProtectedRoute";
import ConnexionVerification from "./pages/Authenticated/flowpages/Connectionrelatedpages/makeconnections/page";
import ConnectionNotification from "./pages/Authenticated/flowpages/notificationpages/Connectionnotification/page";
import InitiationNotification from "./pages/Authenticated/flowpages/notificationpages/intitiationnotification/page";
import ConnectionStatusNotification from "./pages/Authenticated/flowpages/notificationpages/Connectionstatus/page";

const clientId = "719395873709-ese7vg45i9gfndador7q6rmq3untnkcr.apps.googleusercontent.com";

const AppRoutes: React.FC = () => {
  console.log("AppRoutes component is mounted!");
  return (
    <GoogleOAuthProvider clientId={clientId}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<Registration />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
          <Route path="/waiting" element={<Waitingpage />} />
          
          <Route path="/" element={<ProtectedRoute />}>
            <Route path="/" element={<Mainbar />}>
              <Route path="home" element={<HomePage />} />
              <Route path="make-connections" element={<ConnexionVerification />} />
              
              {/* Notification Routes */}
              <Route path="Initiationnotifications/:notificationNumber" 
                     element={<InitiationNotification />} />
              <Route path="Connectionnotifications/:notificationNumber" 
                     element={<ConnectionNotification />} />
              <Route path="ConnectionStatusNotifications/:notificationNumber"
                     element={<ConnectionStatusNotification />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </GoogleOAuthProvider>
  );
};

export default AppRoutes;