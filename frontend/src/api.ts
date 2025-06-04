import axios from "axios";
import handleLogout from "./login/logout";

// Create axios instance (no type casting needed)
const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
});

// Attach access token before each request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      // Ensure headers object exists
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 errors and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Check for 401 error and retry flag
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token available");

        // Add type to POST response
        const res = await axios.post<{ access: string }>(
          "http://127.0.0.1:8000/api/users/token/refresh/",
          { refresh: refreshToken }
        );

        localStorage.setItem("access_token", res.data.access);
        
        // Update default headers
        api.defaults.headers.common = {
          ...api.defaults.headers.common,
          Authorization: `Bearer ${res.data.access}`,
        };

        return api(originalRequest);
      } catch (refreshError) {
        console.log("Session expired, logging out...");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user_id");

        handleLogout();
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export default api;