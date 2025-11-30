// src/utils/logoutHandler.ts
import { getApiUrl } from '../pages/Unauthenticated/config';
import { logout } from "./login_logoutSlice";
import { clearAllTimelines } from "../pages/Authenticated/Timelinepage/timelineSlice";
import { clearAllHeartbeatData } from "../pages/Authenticated/heartbeat/heartbeatSlice";
import { resetChatList } from "../pages/Authenticated/messages/chatlist/chatListSlice";
import { resetContacts } from "../pages/Authenticated/messages/chatlist/contacts/contactsSlice";
import { resetChat } from "../pages/Authenticated/messages/ChatPage/chatSlice";

const handleLogout = async (): Promise<void> => {
    const { persistor } = await import("../store");
    const { store } = await import("../store");

    // Get user_id from local storage
    const userId = localStorage.getItem("user_id");

    if (userId) {
        try {
            // Use getApiUrl to construct the full logout URL
            const logoutUrl = getApiUrl('/api/users/logout/');
            console.log('🔧 Logout URL:', logoutUrl);
            
            // Send logout request to API
            await fetch(logoutUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ user_id: userId }),
            });
        } catch (error) {
            console.error("Logout request failed:", error);
        }
    }

    // Enhanced logout sequence with better cleanup

    // ✅ FIRST: Clear timeline data from Redux store
    store.dispatch(clearAllTimelines());
    
    // ✅ SECOND: Clear heartbeat data from Redux store
    store.dispatch(clearAllHeartbeatData());
    
    // ✅ THIRD: Clear all chat-related data from Redux store
    store.dispatch(resetChatList());
    store.dispatch(resetContacts());
    store.dispatch(resetChat());
    
    // ✅ FOURTH: Clear blog data from Redux store - ENHANCED
    const { clearBlogs } = await import("../pages/Authenticated/blogrelated/blogpage/blogSlice");
    store.dispatch(clearBlogs());
    console.log('✅ Blog data cleared from Redux store');
    
    // ✅ FIFTH: Clear milestones data from Redux store
    const { clearMilestones } = await import("../pages/Authenticated/milestone/milestonesSlice");
    store.dispatch(clearMilestones());
    
    // ✅ SIXTH: Clear notifications data from Redux store
    const { resetNotifications } = await import("../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsSlice");
    store.dispatch(resetNotifications());
    
    // ✅ SEVENTH: Clear any other cached data
    // Add any other data cleanup actions here
    
    // ✅ EIGHTH: Dispatch logout to clear user state
    store.dispatch(logout());
    
    // ✅ NINTH: Purge persisted store
    console.log('🧹 Purging persisted store...');
    await persistor.purge();
    
    // ✅ TENTH: Clear local storage and session storage
    console.log('🧹 Clearing browser storage...');
    localStorage.clear();
    sessionStorage.clear();
    
    // ✅ FINALLY: Reload the page to ensure clean state
    console.log('🔄 Reloading page...');
    window.location.reload();
};

export default handleLogout;