// src/AppRoutes.tsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
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

import MyGroupsPage from "./pages/Authenticated/mygroups/mygroupslist";
import GroupSetupPage from "./pages/Authenticated/mygroups/GroupSetupPage/GroupSetupPage";
import GroupDetailsPage from "./pages/Authenticated/mygroups/GroupDetailsPage/GroupDetailsPage";

import TimelinePage from "./pages/Authenticated/Timelinepage/TimelinePage";
import ChildrenPage from "./pages/Authenticated/children_and_connection_pages/ChildrenPage";
import ConnectionPage from "./pages/Authenticated/children_and_connection_pages/ConnectionsPage";
import BreakdownIdPage from "./pages/Authenticated/Idpage/BreakdownIdPage";

import ReportsListPage from "./pages/Authenticated/dashboard/intitation_reportslist/ReportsListPage";
import DashboardsPage from "./pages/Authenticated/dashboard/dashboard/DashboardsPage";
import ReportViewPage from "./pages/Authenticated/dashboard/reportview/ReportViewPage";
import OverallReportPage from "./pages/Authenticated/dashboard/OverallReportPage/OverallReportPage";
import ActivityReportViewPage from "./pages/Authenticated/dashboard/activityreportview/ActivityReportViewpage";
import ActivityReportListPage from "./pages/Authenticated/dashboard/activityreportslist/ActivityReportListPage";

import HeartbeatPage from "./pages/Authenticated/heartbeat/HeartbeatPage";

import ChatList from "./pages/Authenticated/messages/chatlist/chatlist";
import ChatPage from "./pages/Authenticated/messages/ChatPage/ChatPage";

import MilestonePage from "./pages/Authenticated/milestone/MilestonePage";
import MilestonePreviewPage from "./pages/Authenticated/milestone/MilestonePreviewPage";
import BlogCreator from "./pages/Authenticated/blogrelated/BlogCreator/index";
import ClaimContributionForm from "./pages/Authenticated/contribution/ClaimContributionForm";

const clientId = "719395873709-ese7vg45i9gfndador7q6rmq3untnkcr.apps.googleusercontent.com";

const AppRoutes: React.FC = () => {
  console.log("AppRoutes component is mounted!");

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <Routes>
        {/* Public Routes */}
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
            <Route path="Initiationnotifications/:notificationNumber" element={<InitiationNotification />} />
            <Route path="Connectionnotifications/:notificationNumber" element={<ConnectionNotification />} />
            <Route path="ConnectionStatusNotifications/:notificationNumber" element={<ConnectionStatusNotification />} />
            <Route path="GroupSpeakerInvitation/:notificationNumber" element={<GroupSpeakerInvitation />} />

            <Route path="group-registration" element={<GroupRegistrationForm />} />
            <Route path="my-groups" element={<MyGroupsPage />} />
            <Route path="group/setup/:groupId" element={<GroupSetupPage />} />
            <Route path="group/:groupId" element={<GroupDetailsPage />} />
            <Route path="timeline/:timelineNumber" element={<TimelinePage />} />
            <Route path="children/:id" element={<ChildrenPage />} />
            <Route path="connections/:id" element={<ConnectionPage />} />
            <Route path="breakdown-id" element={<BreakdownIdPage />} />

            <Route path="reports-list" element={<ReportsListPage />} />
            <Route path="dashboards" element={<DashboardsPage />} />
            <Route path="reports/:period/:reportId/:level" element={<ReportViewPage />} />
            <Route path="reports/overall" element={<OverallReportPage />} />
            <Route path="reports/overall/:level/:entityId" element={<OverallReportPage />} />
            <Route path="activity-reports/:period/:reportId/:level" element={<ActivityReportViewPage />} />
            <Route path="activity-reports-list" element={<ActivityReportListPage />} />

            <Route path="messages/chatlist" element={<ChatList />} />
            <Route path="chat/:conversationId" element={<ChatPage />} />
            <Route path="milestones" element={<MilestonePage />} />
            <Route path="milestone-preview" element={<MilestonePreviewPage />} />
            <Route path="blog-creator" element={<BlogCreator />} />
            <Route path="claim-contribution" element={<ClaimContributionForm />} />
          </Route>
        </Route>
      </Routes>
    </GoogleOAuthProvider>
  );
};

export default AppRoutes;
