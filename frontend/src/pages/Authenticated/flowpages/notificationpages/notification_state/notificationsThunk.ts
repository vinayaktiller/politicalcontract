// notificationsThunk.ts (FIXED)
import { Dispatch } from '@reduxjs/toolkit';
import { AppDispatch, RootState } from '../../../../../store';
import {
  addNotification,
  removeNotificationByDetails,
  setConnected,
  setSocket,
} from './notificationsSlice';
import { fetchUserMilestones } from '../../../milestone/milestonesSlice';
import { getWsUrl } from '../../../../Unauthenticated/config';

// Import handler registry and handlers
import { 
  createHandlerRegistry, 
  handleWebSocketMessage 
} from './handlers/handlerRegistry';

// WebSocket connection management
const RECONNECT_BASE_DELAY = 1000;
const MAX_RECONNECT_ATTEMPTS = 5;
let reconnectAttempts = 0;
let currentReconnectAttempts = 0;
let reconnectTimeoutId: NodeJS.Timeout | null = null;

const getReconnectDelay = () => {
  const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
  return Math.min(delay, 30000);
};

// Cleanup function
const cleanupWebSocket = (socket: WebSocket | null) => {
  if (socket) {
    socket.onopen = null;
    socket.onmessage = null;
    socket.onclose = null;
    socket.onerror = null;
  }
};

// Milestone notification handler
const handleMilestoneNotification = (
  data: any,
  dispatch: Dispatch,
  socket: WebSocket
) => {
  console.log('Milestone Notification received:', data.notification);
  
  const milestoneNotification = {
    notification_type: 'Milestone_Notification' as const,
    notification_message: data.notification.notification_message,
    notification_data: data.notification.notification_data,
    notification_number: data.notification.notification_number,
    notification_freshness: data.notification.notification_freshness,
    created_at: data.notification.created_at,
  };

  dispatch(addNotification(milestoneNotification));

  // Send deletion command to server
  const deletionMessage = JSON.stringify({
    action: 'delete_notification',
    notification_type: 'Milestone_Notification',
    notification_number: data.notification.notification_number,
  });

  if (socket.readyState === WebSocket.OPEN) {
    socket.send(deletionMessage);
    console.log('Sent deletion message for Milestone notification');
  }
};

// Main WebSocket connection thunk (FIXED MESSAGE HANDLING)
export const connectWebSocket =
  (userId: string) => async (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();

    // Clear any existing reconnection timeout
    if (reconnectTimeoutId) {
      clearTimeout(reconnectTimeoutId);
      reconnectTimeoutId = null;
    }

    // Avoid duplicate connections
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
      console.log('WebSocket connecting...');
      
      // Use centralized WebSocket URL configuration
      const wsUrl = getWsUrl('/ws/notifications/', userId);
      const socket = new WebSocket(`${wsUrl}/?token=${authToken}`);

      // Create handler registry
      const handlerRegistry = createHandlerRegistry();

      socket.onopen = () => {
        currentReconnectAttempts = 0;
        reconnectAttempts = 0;
        dispatch(setConnected(true));

        // Fetch milestones on connect if idle
        const storedUserId = localStorage.getItem('user_id');
        if (storedUserId) {
          const uid = parseInt(storedUserId, 10);
          const milestoneState = getState().milestones;
          const status = milestoneState?.status || 'idle';
          if (status === 'idle') {
            dispatch(fetchUserMilestones(uid));
          }
        }

        // Notify server that user is online
        socket.send(JSON.stringify({
          category: 'chat_system',
          action: 'user_online',
        }));
      };

      socket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);

          // === Blog Unshare Handling ===
          if (data.type === "blog_unshared") {
            console.log('Blog unshare received:', data);
            const fixedData = {
              ...data,
              blog_id: data.blog_id,
              action: data.action || 'unshared',
              shared_by_user_id: data.shared_by_user_id,
              original_author_id: data.original_author_id,
              user_id: data.user_id,
              shares_count: data.shares_count || 0
            };
            handleWebSocketMessage(fixedData, dispatch, getState, handlerRegistry);
            return;
          }

          // === Blog Creation Handling ===
          if (data.type === "blog_created") {
            console.log('Blog creation received:', data);
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
            return;
          }

          // === Blog Share Handling ===
          if (data.type === "blog_shared") {
            console.log('Blog share received:', data);
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
            return;
          }

          // === Blog Update Handling (for likes/shares) ===
          if (data.type === 'blog_update') {
            console.log('Blog update received:', data);
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
            return;
          }

          // === Blog Modification Handling (FIXED - This was the main issue) ===
          if (data.type === 'blog_modified') {
            console.log('Blog modified received:', data);
            // Ensure the data structure is correct for the handler
            const modifiedData = {
              ...data,
              blog_id: data.blog_id,
              blog: data.blog,
              user_id: data.user_id,
              blog_type: 'circle' // Add blog_type since handler expects it
            };
            handleWebSocketMessage(modifiedData, dispatch, getState, handlerRegistry);
            return;
          }

          // === Blog Comment Handling ===
          if (data.type === 'comment_update') {
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
            return;
          }

          // === Blog Comment Like Handling ===
          if (data.type === 'comment_like_update') {
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
            return;
          }

          // === Reply Update Handling ===
          if (data.type === 'reply_update') {
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
            return;
          }

          // === Milestone Notification Handling ===
          if (data?.notification?.notification_type === 'Milestone_Notification') {
            console.log('Milestone Notification received:', data.notification);
            handleMilestoneNotification(data, dispatch, socket);
            return;
          }

          // === Chat System and Other Notification Messages ===
          if (data?.type === 'notification_message' && data?.category === 'chat_system') {
            handleWebSocketMessage(data, dispatch, getState, handlerRegistry);
          } else if (data?.notification) {
            dispatch(addNotification(data.notification));
          } else if (data?.delete_notification) {
            const { notification_type, notification_number } = data.delete_notification;
            if (notification_type && notification_number) {
              dispatch(
                removeNotificationByDetails({
                  notification_type,
                  notification_number,
                })
              );
            }
          }
        } catch (error) {
          console.error('Message parsing error:', error);
        }
      };

      socket.onclose = (event: CloseEvent) => {
        dispatch(setConnected(false));
        
        // Don't reconnect for normal closures or auth failures
        if ([1000, 4000, 4001].includes(event.code)) {
          console.log('WebSocket closed normally, not reconnecting');
          return;
        }
        
        // Limit reconnection attempts
        if (currentReconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          console.log('Max reconnection attempts reached');
          return;
        }
        
        currentReconnectAttempts++;
        const delay = getReconnectDelay();
        
        console.log(`WebSocket closed. Reconnecting in ${delay}ms (attempt ${currentReconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        
        reconnectTimeoutId = setTimeout(() => {
          const storedUserId = localStorage.getItem('user_id');
          if (storedUserId) dispatch(connectWebSocket(storedUserId) as any);
        }, delay);
      };

      socket.onerror = (error: Event) => {
        console.error('WebSocket error:', error);
        socket.close();
      };

      dispatch(setSocket(socket));
    } catch (error) {
      console.error('Connection failed:', error);
      const delay = getReconnectDelay();
      reconnectTimeoutId = setTimeout(() => dispatch(connectWebSocket(userId) as any), delay);
    }
  };

// Disconnect WebSocket thunk
export const disconnectWebSocket =
  () => (dispatch: AppDispatch, getState: () => RootState) => {
    // Clear any pending reconnection
    if (reconnectTimeoutId) {
      clearTimeout(reconnectTimeoutId);
      reconnectTimeoutId = null;
    }
    
    reconnectAttempts = 0;
    currentReconnectAttempts = 0;

    const { notifications } = getState();
    if (notifications.socket) {
      cleanupWebSocket(notifications.socket);
      notifications.socket.close(4000, 'User initiated disconnect');
      dispatch(setSocket(null));
      dispatch(setConnected(false));
    }
  };

// Send Message Over WebSocket Thunk
export const sendWebSocketMessage =
  (notificationType: string, messagetype: string, data: Record<string, any>) =>
  (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();
    if (notifications.socket && notifications.socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ notificationType, messagetype, ...data });
      notifications.socket.send(message);
    } else {
      console.error('WebSocket is not connected');
      const storedUserId = localStorage.getItem('user_id');
      if (storedUserId) dispatch(connectWebSocket(storedUserId) as any);
    }
  };