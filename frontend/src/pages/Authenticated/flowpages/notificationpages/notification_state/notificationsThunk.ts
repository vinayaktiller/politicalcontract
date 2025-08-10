// src/features/notifications/notificationsThunk.ts

import { Dispatch } from '@reduxjs/toolkit';
import { AppDispatch, RootState } from '../../../../../store';
import {
  addNotification,
  removeNotificationByDetails,
  setConnected,
  setSocket,
} from './notificationsSlice';
import { addMessage, updateMessage } from '../../../messages/ChatPage/chatSlice';
import { updateConversation } from '../../../messages/chatlist/chatListSlice';
import { fetchUserMilestones, addMilestone } from '../../../milestone/milestonesSlice';

const RECONNECT_BASE_DELAY = 1000;
let reconnectAttempts = 0;

const getReconnectDelay = () => {
  const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
  return Math.min(delay, 30000);
};

const handleChatSystemMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const subtype = data.subtype;
  const conversationId = data.conversation_id;
  const messageId = data.message_id;
  const status = data.status;

  switch (subtype) {
    case 'new_message': {
      const state = getState();
      const conversation = state.chat.rooms[conversationId]?.conversation;
      const room = state.chat.rooms[conversationId];
      const isCurrentRoom = state.chat.currentRoomId === conversationId;

      // Deduplication: ignore if message ID already exists
      if (room && room.messages.some(m => m.id === messageId)) {
        console.log(`Duplicate new_message ignored for messageID: ${messageId}`);
        break;
      }

      let sender_name = 'Unknown';
      let sender_profile = null;
      if (conversation) {
        if (conversation.other_user.id === data.sender_id) {
          sender_name = conversation.other_user.name;
          sender_profile = conversation.other_user.profile_pic;
        }
      }

      const message = {
        id: messageId,
        content: data.content,
        timestamp: data.timestamp,
        status: data.status || 'sent',
        sender_name: data.sender_name || sender_name,
        sender_profile: data.sender_profile || sender_profile,
        is_own: false,
      };

      dispatch(addMessage({ conversationId, message }));

      // Update chat list conversation info
      const currentUnreadCount = state.chatList.entities[conversationId]?.unread_count || 0;
      dispatch(updateConversation({
        id: conversationId,
        changes: {
          last_message: data.content,
          last_message_timestamp: data.timestamp,
          unread_count: isCurrentRoom ? currentUnreadCount : currentUnreadCount + 1,
        },
        moveToTop: true,
      }));

      break;
    }

    case 'message_delivered':
    case 'delivered_update':
    case 'message_read':
    case 'read_update':
    case 'message_read_update':
      dispatch(updateMessage({
        conversationId,
        messageId,
        changes: { status },
      }));
      break;

    case 'message_sent':
      dispatch(updateMessage({
        conversationId,
        messageId: data.temp_id,
        changes: {
          id: data.message_id,
          status: data.status || 'sent',
          timestamp: data.timestamp,
        },
      }));
      break;

    default:
      console.warn('Unhandled chat subtype:', subtype);
  }
};

export const connectWebSocket =
  (userId: string) => async (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();

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
      const socket = new WebSocket(
        `ws://localhost:8000/ws/notifications/${userId}/?token=${authToken}`
      );

      socket.onopen = () => {
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

        socket.send(JSON.stringify({
          category: 'chat_system',
          action: 'user_online',
        }));
      };

      socket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);

          // === Milestone Notification Handling ===
          if (data?.notification?.notification_type === 'Milestone_Notification') {
            console.log('Milestone Notification received:', data.notification);
            // Create UI notification
            const milestoneNotification = {
              notification_type: 'Milestone_Notification' as const,
              notification_message: data.notification.notification_message,
              notification_data: data.notification.notification_data,
              notification_number: data.notification.notification_number,
              notification_freshness: data.notification.notification_freshness,
              created_at: data.notification.created_at
            };
            console.log('Dispatching Milestone Notification:', milestoneNotification);

            dispatch(addNotification(milestoneNotification));

            // === NEW: Send deletion command to server for this milestone notification ===
            const deletionMessage = JSON.stringify({
              action: 'delete_notification',
              notification_type: 'Milestone_Notification',
              notification_number: data.notification.notification_number
            });

            if (socket.readyState === WebSocket.OPEN) {
              socket.send(deletionMessage);
              console.log('Sent deletion message for Milestone notification:', deletionMessage);
            }

            return;
          }

          // === Existing handlers ===
          if (data?.type === 'notification_message' && data?.category === 'chat_system') {
            handleChatSystemMessage(data, dispatch, getState);
          } else if (data?.notification) {
            dispatch(addNotification(data.notification));
          } else if (data?.delete_notification) {
            const { notification_type, notification_number } = data.delete_notification;
            if (notification_type && notification_number) {
              dispatch(removeNotificationByDetails({
                notification_type,
                notification_number,
              }));
            }
          }
        } catch (error) {
          console.error('Message parsing error:', error);
        }
      };

      socket.onclose = (event: CloseEvent) => {
        dispatch(setConnected(false));
        if (![4000, 4001].includes(event.code)) {
          reconnectAttempts++;
          const delay = getReconnectDelay();
          setTimeout(() => {
            const storedUserId = localStorage.getItem('user_id');
            if (storedUserId) dispatch(connectWebSocket(storedUserId) as any);
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

export const disconnectWebSocket =
  () => (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();
    if (notifications.socket) {
      notifications.socket.close(4000, 'User initiated disconnect');
      dispatch(setSocket(null));
      dispatch(setConnected(false));
    }
  };

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
