import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../store';
import {
  setActiveUsersCount,
  setTotalUsersCount,
  setActiveError,
  setTotalError,
  startActiveLoading,
  startTotalLoading
} from './activeUsersSlice';
import { getWsUrl } from '../../../../Unauthenticated/config';

let socket: WebSocket | null = null;
let reconnectTimeout: NodeJS.Timeout | null = null;
let heartbeatInterval: NodeJS.Timeout | null = null;
let inactivityTimer: NodeJS.Timeout | null = null;

const RECONNECT_BASE_DELAY = 1000;
const INACTIVITY_LIMIT_MS = 5 * 60 * 1000; // 5 minutes inactivity limit

const getReconnectDelay = (attempts: number) => {
  const delay = RECONNECT_BASE_DELAY * Math.pow(2, attempts);
  return Math.min(delay, 30000);
};

const setupHeartbeat = () => {
  if (heartbeatInterval) clearInterval(heartbeatInterval);

  heartbeatInterval = setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'ping' }));
    }
  }, 15000);
};

const resetInactivityTimer = (dispatch: Dispatch) => {
  if (inactivityTimer) clearTimeout(inactivityTimer);
  inactivityTimer = setTimeout(() => {
    console.log('No user activity for 5 minutes, disconnecting WebSocket');
    dispatch(disconnectWebSocket() as any);
  }, INACTIVITY_LIMIT_MS);
};

const setupInactivityListeners = (dispatch: Dispatch) => {
  const events = ['mousemove', 'keydown', 'scroll', 'touchstart'];
  const handleActivity = () => resetInactivityTimer(dispatch);

  events.forEach(event => window.addEventListener(event, handleActivity));
  resetInactivityTimer(dispatch);

  return () => {
    events.forEach(event => window.removeEventListener(event, handleActivity));
    if (inactivityTimer) clearTimeout(inactivityTimer);
  };
};

export const connectWebSocket = () =>
  async (dispatch: Dispatch, getState: () => RootState) => {
    // Start both loading indicators
    dispatch(startActiveLoading());
    dispatch(startTotalLoading());

    try {
      // Close existing socket if it exists
      if (socket) {
        socket.close(4001, 'Reconnecting');
        socket = null;
      }
      
      // Use centralized WebSocket URL configuration
      const wsUrl = getWsUrl('/ws/activity/today/');
      const newSocket = new WebSocket(wsUrl);
      socket = newSocket;

      // Setup inactivity listeners and get cleanup function
      const removeInactivityListeners = setupInactivityListeners(dispatch);

      newSocket.onopen = () => {
        console.log('[WebSocket] Connection opened');
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
        // Clear errors for both
        dispatch(setActiveError(''));
        dispatch(setTotalError(''));
        setupHeartbeat();
      };

      newSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Ignore pong messages
          if (data.type === 'pong') return;

          // Handle different update types
          if (data.update_type === 'active_users' && typeof data.count === 'number') {
            console.log('[WebSocket] Received active users update:', data.count);
            dispatch(setActiveUsersCount(data.count));
          }
          else if (data.update_type === 'petitioners' && typeof data.count === 'number') {
            console.log('[WebSocket] Received petitioner count update:', data.count);
            dispatch(setTotalUsersCount(data.count));
          }
          else {
            console.error('Invalid WebSocket message format:', data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error, event.data);
        }
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        dispatch(setActiveError('Connection error'));
        dispatch(setTotalError('Connection error'));
      };

      newSocket.onclose = (event) => {
        console.log(`[WebSocket] Connection closed: ${event.code} - ${event.reason}`);
        if (event.code === 4000 || event.code === 4001) {
          // Intentional close, clean up inactivity listeners and heartbeat
          if (removeInactivityListeners) removeInactivityListeners();
          if (heartbeatInterval) clearInterval(heartbeatInterval);
          heartbeatInterval = null;
          return;
        }

        dispatch(setActiveError('Connection closed'));
        dispatch(setTotalError('Connection closed'));

        if (removeInactivityListeners) removeInactivityListeners();
        if (heartbeatInterval) clearInterval(heartbeatInterval);
        heartbeatInterval = null;

        const attempts = reconnectTimeout ? 1 : 0;
        const delay = getReconnectDelay(attempts);

        reconnectTimeout = setTimeout(() => {
          console.log(`[WebSocket] Attempting reconnect after ${delay}ms`);
          dispatch(connectWebSocket() as any);
        }, delay);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      dispatch(setActiveError('Connection failed'));
      dispatch(setTotalError('Connection failed'));

      const attempts = reconnectTimeout ? 1 : 0;
      const delay = getReconnectDelay(attempts);
      reconnectTimeout = setTimeout(() => dispatch(connectWebSocket() as any), delay);
    }
  };

export const disconnectWebSocket = () =>
  (dispatch: Dispatch, getState: () => RootState) => {
    if (socket) {
      socket.close(4000, 'User initiated disconnect');
      socket = null;
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
  };