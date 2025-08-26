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

// Set baseURL to your backend server
const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
interface FailedQueueItem {
  resolve: (value?: unknown) => void;
  reject: (reason?: any) => void;
}

let failedQueue: FailedQueueItem[] = [];

interface ProcessQueuePromise {
  resolve: (value?: unknown) => void;
  reject: (reason?: any) => void;
}

type ProcessQueueError = unknown;
type ProcessQueueToken = string | null;

const processQueue = (
  error: ProcessQueueError,
  token: ProcessQueueToken = null
): void => {
  failedQueue.forEach((prom: ProcessQueuePromise) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is 401 and it's not a refresh request
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If we're already refreshing, add the request to the queue
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        // Attempt to refresh the token
        await api.post('/api/users/token/refresh-cookie/');
        
        // Process the queue
        processQueue(null, null);
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, process the queue with error
        processQueue(refreshError, null);
        
        // Logout the user
        handleLogout();
        window.location.reload();
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;