import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../store';
import { addNotification, setSocket, setConnected, removeNotificationByDetails } from './notificationsSlice';

const RECONNECT_BASE_DELAY = 1000;
let reconnectAttempts = 0;

const getReconnectDelay = () => {
  const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
  return Math.min(delay, 30000);
};

export const connectWebSocket =
  (userId: string) => async (dispatch: Dispatch, getState: () => RootState) => {
    const { notifications } = getState();
    
    if (notifications.socket instanceof WebSocket) {
      const socket = notifications.socket;
      if (socket.readyState === WebSocket.CONNECTING) {
        socket.close(4000, 'New connection attempt');
        return;
      }
      if (socket.readyState === WebSocket.OPEN) {
        return;
      }
    }

    try {
      const authToken = localStorage.getItem('access_token');
      const socket = new WebSocket(
        `ws://localhost:8000/ws/notifications/${userId}/?token=${authToken}`
      );

      socket.onopen = () => {
        reconnectAttempts = 0;
        dispatch(setConnected(true));
        console.log('WebSocket connected');
      };

      // In your WebSocket setup file
      socket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data?.notification) {
            console.log('Received notification:', data.notification);
            dispatch(addNotification(data.notification));
          }
          else if (data?.delete_notification) {
            console.log('Received delete notification:', data.delete_notification);
            
            const { notification_type, notification_number } = data.delete_notification;
            
            if (notification_type && notification_number) {
              dispatch(removeNotificationByDetails({ 
                notification_type, 
                notification_number 
              }));
            } else {
              console.error('Invalid delete notification format:', data.delete_notification);
            }
          }
        } catch (error) {
          console.error('Message parsing error:', error);
        }
      };

      socket.onclose = (event: CloseEvent) => {
        dispatch(setConnected(false));

        switch(event.code) {
          case 4000:
          case 4001:
            return;
          default:
            reconnectAttempts++;
            const delay = getReconnectDelay();
            console.log(`Reconnecting in ${delay/1000} seconds...`);
            setTimeout(() => {
              const userId = localStorage.getItem('user_id');
              if (userId) dispatch(connectWebSocket(userId) as any);
            }, delay);
        }
      };

      socket.onerror = (error: Event) => {
        console.error('WebSocket error:', error);
        socket.close();
      };

      dispatch(setSocket(socket));

    } catch (error) {
      console.error('Connection failed:', error);
      const delay = getReconnectDelay();
      setTimeout(() => dispatch(connectWebSocket(userId) as any), delay);
    }
  };

export const disconnectWebSocket = () => (dispatch: Dispatch, getState: () => RootState) => {
  const { notifications } = getState();
  if (notifications.socket) {
    notifications.socket.close(4000, 'User initiated disconnect');
    dispatch(setSocket(null));
    dispatch(setConnected(false));
  }
};

export const sendWebSocketMessage =
  (notificationType: string,messagetype: string, data: Record<string, any>) =>
  (dispatch: Dispatch, getState: () => RootState) => {
    const { notifications } = getState();
    
    if (notifications.socket && notifications.socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ notificationType,messagetype, ...data });
      notifications.socket.send(message);
    } else {
      console.error('WebSocket is not connected');
      const userId = localStorage.getItem('user_id');
      if (userId) dispatch(connectWebSocket(userId) as any);
    }
  };

// TypeScript-specific imports for browser-based WebSocket handling
// No extra npm package is required for WebSocket in the browser

// In browser environments, you do NOT need to import MessageEvent or CloseEvent explicitly

// import type { AppDispatch } from '../../../../../store';

// let socket: WebSocket | null = null;
// export const connectWebSocket = (userId: string) => (dispatch: AppDispatch) => {
  

//   socket = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}/`);

//   socket.onopen = () => {
//     console.log("WebSocket connected");
//   };

//   socket.onmessage = (event: MessageEvent) => {
//     console.log("Received message:", event.data);
//   };

//   socket.onclose = (event: CloseEvent) => {
//     console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
//     socket = null;
//   };

//   socket.onerror = (error: Event) => {
//     console.error("WebSocket error:", error);
//   };
// };

// export const disconnectWebSocket = () => (dispatch: AppDispatch) => {
//   if (socket) {
//     socket.close(4000, "Manual disconnect");
//     socket = null;
//     console.log("WebSocket disconnected");
//   } else {
//     console.log("WebSocket is not connected");
//   }
// };

// export const sendWebSocketMessage = (type: string, data: Record<string, any>) => {
//   if (socket && socket.readyState === WebSocket.OPEN) {
//     const message = JSON.stringify({ type, ...data });
//     socket.send(message);
//     console.log("Sent message:", message);
//   } else {
//     console.error("Cannot send message. WebSocket is not open.");
//   }
// };
