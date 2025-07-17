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

let socket: WebSocket | null = null;
let reconnectTimeout: NodeJS.Timeout | null = null;
let heartbeatInterval: NodeJS.Timeout | null = null;

const RECONNECT_BASE_DELAY = 1000;

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

      const newSocket = new WebSocket(`ws://${window.location.hostname}:8000/ws/activity/today/`);
      socket = newSocket;

      newSocket.onopen = () => {
        console.log("[WebSocket] Connection opened");
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
            console.log("[WebSocket] Received active users update:", data.count);
            dispatch(setActiveUsersCount(data.count));
          } 
          else if (data.update_type === 'petitioners' && typeof data.count === 'number') {
            console.log("[WebSocket] Received petitioner count update:", data.count);
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
        // Set errors for both counts
        dispatch(setActiveError('Connection error'));
        dispatch(setTotalError('Connection error'));
      };

      newSocket.onclose = (event) => {
        console.log(`[WebSocket] Connection closed: ${event.code} - ${event.reason}`);
        if (event.code === 4000 || event.code === 4001) {
          return; // Intentional close
        }
        
        // Set errors for both counts
        dispatch(setActiveError('Connection closed'));
        dispatch(setTotalError('Connection closed'));
        
        // Reconnect with backoff
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
  };