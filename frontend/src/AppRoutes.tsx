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
import GroupSpeakerInvitation from "./pages/Authenticated/flowpages/notificationpages/GroupSpeakerInvitation/page";
import GroupRegistrationForm from "./pages/Authenticated/flowpages/Groupregistration/GroupRegistrationForm";
import MyGroupsPage from "./pages/Authenticated/mygroups/mygroupslist"; // Adjust the import path as necessary
import GroupSetupPage from "./pages/Authenticated/mygroups/GroupSetupPage/GroupSetupPage"; // Adjust the import path as necessary
import GroupDetailsPage from "./pages/Authenticated/mygroups/GroupDetailsPage/GroupDetailsPage"; // Adjust the import path as necessary
import TimelinePage from "./pages/Authenticated/Timelinepage/TimelinePage"; // Adjust the import path as necessary
import ChildrenPage from "./pages/Authenticated/children_and_connection_pages/ChildrenPage"; // Adjust the import path as necessary
import ConnectionPage from "./pages/Authenticated/children_and_connection_pages/ConnectionsPage"; // Adjust the import path as necessary
import BreakdownIdPage from "./pages/Authenticated/Idpage/BreakdownIdPage"; // Adjust the import path as necessary
import ReportsListPage from "./pages/Authenticated/dashboard/intitation_reportslist/ReportsListPage"; // Adjust the import path as necessary
import DashboardsPage from "./pages/Authenticated/dashboard/dashboard/DashboardsPage"; // Adjust the import path as necessary
import ReportViewPage from "./pages/Authenticated/dashboard/reportview/ReportViewPage"; // Adjust the import path as necessary
import OverallReportPage from "./pages/Authenticated/dashboard/OverallReportPage/OverallReportPage"; // Adjust the import path as necessary
import ActivityReportViewPage from "./pages/Authenticated/dashboard/activityreportview/ActivityReportViewpage"; // Adjust the import path as necessary
import ActivityReportListPage from "./pages/Authenticated/dashboard/activityreportslist/ActivityReportListPage"; // Adjust the import path as necessary
import HeartbeatPage from "./pages/Authenticated/heartbeat/HeartbeatPage"; // Adjust the import path as necessary
import ChatList from "./pages/Authenticated/messages/chatlist/chatlist"; // Adjust the import path as necessary
import ChatPage from "./pages/Authenticated/messages/ChatPage/ChatPage"; // Adjust the import path as necessary
const clientId = "719395873709-ese7vg45i9gfndador7q6rmq3untnkcr.apps.googleusercontent.com";

const AppRoutes: React.FC = () => {
  console.log("AppRoutes component is mounted!");
  return (
    <GoogleOAuthProvider clientId={clientId}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<Registration />} />
          <Route path="/waiting" element={<Waitingpage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
          
          {/* Protected routes */}
          <Route path="/" element={<ProtectedRoute />}>
            <Route path="/" element={<Mainbar />}>
              {/* Redirect root to /heartbeat */}
              <Route index element={<Navigate to="/heartbeat" replace />} />
              
              {/* Heartbeat as first/default authenticated route */}
              <Route path="heartbeat" element={<HeartbeatPage />} />
              
              {/* Other authenticated routes */}
              <Route path="home" element={<HomePage />} />
              <Route path="make-connections" element={<ConnexionVerification />} />
              
              {/* Notification Routes */}
              <Route path="Initiationnotifications/:notificationNumber" 
                     element={<InitiationNotification />} />
              <Route path="Connectionnotifications/:notificationNumber" 
                     element={<ConnectionNotification />} />
              <Route path="ConnectionStatusNotifications/:notificationNumber"
                     element={<ConnectionStatusNotification />} />
              <Route path="GroupSpeakerInvitation/:notificationNumber"
                     element={<GroupSpeakerInvitation />} />
              <Route path="group-registration" element={<GroupRegistrationForm />} />
              <Route path="my-groups" element={<MyGroupsPage />} />
              <Route path="/group/setup/:groupId" element={<GroupSetupPage />} />
              <Route path="/group/:groupId" element={<GroupDetailsPage />} />
              <Route path="/timeline/:timelineNumber" element={<TimelinePage />} />
              <Route path="children/:id" element={<ChildrenPage />} />
              <Route path="connections/:id" element={<ConnectionPage />} />
              <Route path="breakdown-id" element={<BreakdownIdPage />} />
              <Route path="reports-list" element={<ReportsListPage />} />
              <Route path="dashboards" element={<DashboardsPage />} />
              <Route path="reports/:period/:reportId/:level" element={<ReportViewPage />} />
              <Route path="/reports/overall" element={<OverallReportPage />} />
              <Route path="/reports/overall/:level/:entityId" element={<OverallReportPage />} />
              <Route path="/activity-reports/:period/:reportId/:level" element={<ActivityReportViewPage />} />
              <Route path="/activity-reports-list" element={<ActivityReportListPage />} />
              <Route path="/messages/chatlist" element={<ChatList />} />
              <Route path="/chat/:conversationId" element={<ChatPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </GoogleOAuthProvider>
  );
};

export default AppRoutes;