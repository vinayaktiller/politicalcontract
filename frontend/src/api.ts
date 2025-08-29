// import axios from "axios";
// import handleLogout from "./login/logout";

// // Create axios instance (no type casting needed)
// const api = axios.create({
//   baseURL: "http://127.0.0.1:8000",
//   headers: { "Content-Type": "application/json" },
// });

// // Attach access token before each request
// api.interceptors.request.use(
//   (config) => {
//     const token = localStorage.getItem("access_token");
//     if (token) {
//       // Ensure headers object exists
//       config.headers = config.headers || {};
//       config.headers.Authorization = `Bearer ${token}`;
//     }
//     return config;
//   },
//   (error) => Promise.reject(error)
// );

// // Handle 401 errors and refresh token
// api.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     const originalRequest = error.config;

//     // Check for 401 error and retry flag
//     if (error.response?.status === 401 && !originalRequest._retry) {
//       originalRequest._retry = true;

//       try {
//         const refreshToken = localStorage.getItem("refresh_token");
//         if (!refreshToken) throw new Error("No refresh token available");

//         // Add type to POST response
//         const res = await axios.post<{ access: string }>(
//           "http://127.0.0.1:8000/api/users/token/refresh/",
//           { refresh: refreshToken }
//         );

//         localStorage.setItem("access_token", res.data.access);
        
//         // Update default headers
//         api.defaults.headers.common = {
//           ...api.defaults.headers.common,
//           Authorization: `Bearer ${res.data.access}`,
//         };

//         return api(originalRequest);
//       } catch (refreshError) {
//         console.log("Session expired, logging out...");
//         localStorage.removeItem("access_token");
//         localStorage.removeItem("refresh_token");
//         localStorage.removeItem("user_id");

//         handleLogout();
//         window.location.reload();
//       }
//     }
//     return Promise.reject(error);
//   }
// );

// export default api;

// api.js - Update baseURL and ensure proper credentials handling
// api.js

// import axios from "axios";
// import handleLogout from "./login/logout";

// const api = axios.create({
//   baseURL: "", // Use empty string for relative paths with proxy
//   headers: { "Content-Type": "application/json" },
//   withCredentials: true,
// });

// api.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     if (error.response?.status === 401) {
//       handleLogout();
//       window.location.reload();
//     }
//     return Promise.reject(error);
//   }
// );

// export default api;

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
