// config.ts
// Centralized configuration for the application

// Debug environment variables
console.log('🔧 Environment Variables Debug:');
console.log('REACT_APP_API_BASE_URL:', process.env.REACT_APP_API_BASE_URL);
console.log('REACT_APP_WS_BASE_URL:', process.env.REACT_APP_WS_BASE_URL);
console.log('REACT_APP_FRONTEND_BASE_URL:', process.env.REACT_APP_FRONTEND_BASE_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('-----------------------------------');

// Determine which values are being used
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://bacfor-pfs-etathmb8gphgf0db.canadacentral-01.azurewebsites.net';
const WS_BASE_URL = process.env.REACT_APP_WS_BASE_URL || 'wss://bacfor-pfs-etathmb8gphgf0db.canadacentral-01.azurewebsites.net';
const FRONTEND_BASE_URL = process.env.REACT_APP_FRONTEND_BASE_URL || 'https://pfs-ui-f7bnfbg9agb4cwcu.canadacentral-01.azurewebsites.net';

console.log('🔧 Final Configuration Values:');
console.log('API_BASE_URL:', API_BASE_URL, process.env.REACT_APP_API_BASE_URL ? '(from env)' : '(using fallback)');
console.log('WS_BASE_URL:', WS_BASE_URL, process.env.REACT_APP_WS_BASE_URL ? '(from env)' : '(using fallback)');
console.log('FRONTEND_BASE_URL:', FRONTEND_BASE_URL, process.env.REACT_APP_FRONTEND_BASE_URL ? '(from env)' : '(using fallback)');
console.log('-----------------------------------');

export const config = {
  // Base URLs
  API_BASE_URL,
  WS_BASE_URL,
  
  // Frontend Base URL for static assets and images
  FRONTEND_BASE_URL,
  
  // Local development URLs (uncomment these and comment the above for local development)
  // API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  // WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000',
  // FRONTEND_BASE_URL: process.env.REACT_APP_FRONTEND_BASE_URL || 'http://localhost:3000',
  
  // API Endpoints - ensure they match your backend exactly
  endpoints: {
    googleAuth: '/api/users/auth/google/',
    landingAuth: '/api/users/auth/landing/', // 🔥 New endpoint for landing page auth
    pushNotification: '/api/users/push-notification/login/',
    testCookie: '/api/users/test-cookie/',
    createPendingUser: '/api/pendingusers/pending-user/create/', // Added trailing slash
    tokenRefresh: '/api/users/token/refresh-cookie/',
  },
  
  // WebSocket paths
  wsPaths: {
    waitingPage: '/ws/waitingpage/',
    activity: '/ws/activity/today/',
    notifications: '/ws/notifications/',
  },
};

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  const fullUrl = `${config.API_BASE_URL}${endpoint}`;
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔧 getApiUrl: ${endpoint} -> ${fullUrl}`);
  }
  return fullUrl;
};

// Helper function to get full WebSocket URL
export const getWsUrl = (path: string, identifier: string = ''): string => {
  const fullUrl = `${config.WS_BASE_URL}${path}${identifier}`;
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔧 getWsUrl: ${path}${identifier} -> ${fullUrl}`);
  }
  return fullUrl;
};

// Helper function to get full frontend asset URL
export const getFrontendUrl = (path: string = ''): string => {
  const fullUrl = `${config.FRONTEND_BASE_URL}${path}`;
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔧 getFrontendUrl: ${path} -> ${fullUrl}`);
  }
  return fullUrl;
};

// Log the final configuration
console.log('🔧 Final Config Object:', {
  API_BASE_URL: config.API_BASE_URL,
  WS_BASE_URL: config.WS_BASE_URL,
  FRONTEND_BASE_URL: config.FRONTEND_BASE_URL,
  endpoints: config.endpoints,
  wsPaths: config.wsPaths
});
console.log('===================================');

export default config;