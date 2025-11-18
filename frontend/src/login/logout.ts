// src/utils/logoutHandler.ts
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
            // Send logout request to API
            await fetch("http://localhost:8000/api/users/logout/", {
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

    // ✅ FIRST: Clear timeline data from Redux store
    store.dispatch(clearAllTimelines());
    
    // ✅ SECOND: Clear heartbeat data from Redux store
    store.dispatch(clearAllHeartbeatData());
    
    // ✅ THIRD: Clear all chat-related data from Redux store
    store.dispatch(resetChatList());
    store.dispatch(resetContacts());
    store.dispatch(resetChat());
    
    // ✅ FOURTH: Clear blog data from Redux store
    const { clearBlogs } = await import("../pages/Authenticated/blogrelated/blogpage/blogSlice");
    store.dispatch(clearBlogs());
    
    // ✅ FIFTH: Clear milestones data from Redux store
    const { clearMilestones } = await import("../pages/Authenticated/milestone/milestonesSlice");
    store.dispatch(clearMilestones());
    
    // ✅ SIXTH: Dispatch logout to clear user state
    store.dispatch(logout());
    
    // ✅ SEVENTH: Purge persisted store
    await persistor.purge();
    
    // ✅ EIGHTH: Clear local storage
    localStorage.clear();
    
    // ✅ FINALLY: Reload the page
    window.location.reload();
};

export default handleLogout;