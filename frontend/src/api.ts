// api.js
import axios from "axios";
import handleLogout from "./login/logout";

// =============================
// Base axios instance for normal API requests
// =============================
const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// =============================
// Separate axios instance for token refresh
// (no interceptors to avoid recursion)
// =============================
const refreshApi = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// =============================
// Queue handling for parallel requests
// =============================
let isRefreshing = false;

interface FailedQueueItem {
  resolve: (value?: unknown) => void;
  reject: (reason?: any) => void;
}
let failedQueue: FailedQueueItem[] = [];

const processQueue = (error: unknown, token: string | null = null): void => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// =============================
// Response interceptor
// =============================
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If unauthorized and request wasn't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If another refresh is happening, wait for it
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (token) {
              originalRequest.headers["Authorization"] = "Bearer " + token;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        console.log("🔄 Attempting to refresh token...");
        await refreshApi.post("/api/users/token/refresh-cookie/");
        console.log("✅ Token refreshed successfully");

        // Wake up pending requests
        processQueue(null, null);

        // Retry the failed request
        return api(originalRequest);
      } catch (refreshError) {
        console.error("❌ Refresh token expired or invalid, logging out...");
        processQueue(refreshError, null);

        handleLogout();
        window.location.reload();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // If not 401, just reject normally
    return Promise.reject(error);
  }
);

export default api;
