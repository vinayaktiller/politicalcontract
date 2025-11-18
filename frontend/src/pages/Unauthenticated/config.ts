// config.ts
// Centralized configuration for the application
export const config = {
  // Base URLs
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'https://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net',
  
  // WebSocket URLs
  WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL || 'wss://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net',
  
  // Local development URLs (uncomment these and comment the above for local development)
  // API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  // WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000',
  
  // API Endpoints - ensure they match your backend exactly
  endpoints: {
    googleAuth: '/api/users/auth/google/',
    landingAuth: '/api/users/auth/landing/', // 🔥 New endpoint for landing page auth
    pushNotification: '/api/users/push-notification/login/',
    testCookie: '/api/users/test-cookie/',
    createPendingUser: '/api/pendingusers/pending-user/create/', // Added trailing slash
  },
  
  // WebSocket paths
  wsPaths: {
    waitingPage: '/ws/waitingpage/',
  },
};

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${config.API_BASE_URL}${endpoint}`;
};

// Helper function to get full WebSocket URL
export const getWsUrl = (path: string, identifier: string = ''): string => {
  return `${config.WS_BASE_URL}${path}${identifier}`;
};

export default config;