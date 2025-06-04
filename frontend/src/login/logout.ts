import { logout } from "./login_logoutSlice"; // Import logout action
const handleLogout = async (): Promise<void> => {
    const { logout } = await import("./login_logoutSlice");
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

    // Proceed with logout actions
    store.dispatch(logout());
    persistor.purge();
    localStorage.clear();
    window.location.reload();
};

export default handleLogout;
