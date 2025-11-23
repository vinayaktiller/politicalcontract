// handlers/chatHandlers.ts
import { Dispatch } from '@reduxjs/toolkit';
import { RootState } from '../../../../../../store';
import { addMessage, updateMessage } from '../../../../messages/ChatPage/chatSlice';
import { updateConversation } from '../../../../messages/chatlist/chatListSlice';
import { addNotification, removeNotificationByDetails } from '../notificationsSlice';
import { MessageNotification } from '../notificationsTypes';
import { MessageHandler } from './handlerRegistry';

// Generic notification handler (for all non-specific notifications)
export const handleGenericNotification: MessageHandler = (data, dispatch, getState) => {
  // Handle general notification messages (from old code: else if (data?.notification))
  if (data.notification) {
    dispatch(addNotification(data.notification));
  }
};

// Notification message handler (for notification_message type)
export const handleNotificationMessage: MessageHandler = (data, dispatch, getState) => {
  // This handles the case where type is 'notification_message' but category is not 'chat_system'
  if (data.notification) {
    dispatch(addNotification(data.notification));
  }
};

// Message notification handler (specific for chat messages)
const handleMessageNotification: MessageHandler = (data, dispatch, getState) => {
  const state = getState();
  const currentRoomId = state.chat.currentRoomId;
  const conversationId = data.conversation_id;
  
  if (currentRoomId === conversationId) return;

  const existingMessageNotification = state.notifications.notifications.find(
    n => n.notification_type === 'Message_Notification'
  ) as MessageNotification | undefined;

  const chatListState = state.chatList;
  const totalUnreadCount = chatListState.ids.reduce((count, id) => {
    const conv = chatListState.entities[id];
    return count + (conv?.unread_count || 0);
  }, 0);

  const conversationCount = chatListState.ids.filter(id => {
    const conv = chatListState.entities[id];
    return conv && conv.unread_count > 0;
  }).length;

  const notificationMessage = `You have ${totalUnreadCount} new messages from ${conversationCount} conversations`;

  if (existingMessageNotification) {
    const updatedNotification: Omit<MessageNotification, 'id'> = {
      notification_type: "Message_Notification",
      notification_message: notificationMessage,
      notification_data: {
        conversation_id: conversationId,
        sender_id: data.sender_id,
        sender_name: data.sender_name,
        message_content: data.content,
        message_count: totalUnreadCount,
        conversation_count: conversationCount,
        timestamp: data.timestamp,
        profile_picture: data.sender_profile || null
      },
      notification_number: existingMessageNotification.notification_number,
      notification_freshness: false
    };

    dispatch(removeNotificationByDetails({
      notification_type: "Message_Notification",
      notification_number: existingMessageNotification.notification_number,
    }));
    
    dispatch(addNotification(updatedNotification));
  } else {
    const messageNotification: Omit<MessageNotification, 'id'> = {
      notification_type: "Message_Notification",
      notification_message: notificationMessage,
      notification_data: {
        conversation_id: conversationId,
        sender_id: data.sender_id,
        sender_name: data.sender_name,
        message_content: data.content,
        message_count: totalUnreadCount,
        conversation_count: conversationCount,
        timestamp: data.timestamp,
        profile_picture: data.sender_profile || null
      },
      notification_number: `message_${Date.now()}`,
      notification_freshness: false
    };
    
    dispatch(addNotification(messageNotification));
  }
};

// Chat system handler
export const handleChatSystemMessage: MessageHandler = (data, dispatch, getState) => {
  const subtype = data.subtype;
  const conversationId = data.conversation_id;
  const messageId = data.message_id;
  const status = data.status;

  switch (subtype) {
    case 'new_message':
      handleNewMessage(data, dispatch, getState);
      break;

    case 'message_delivered':
    case 'delivered_update':
    case 'message_read':
    case 'read_update':
    case 'message_read_update':
      dispatch(updateMessage({ conversationId, messageId, changes: { status } }));
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

// Helper for new message handling
const handleNewMessage = (data: any, dispatch: Dispatch, getState: () => RootState) => {
  const state = getState();
  const conversationId = data.conversation_id;
  const messageId = data.message_id;
  const conversation = state.chat.rooms[conversationId]?.conversation;
  const room = state.chat.rooms[conversationId];
  const isCurrentRoom = state.chat.currentRoomId === conversationId;

  // Deduplication
  if (room && room.messages.some((m: any) => m.id === messageId)) {
    console.log(`Duplicate new_message ignored for messageID: ${messageId}`);
    return;
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

  // ✅ FIXED: Call message notification if not in current room (from old code)
  if (!isCurrentRoom) {
    handleMessageNotification(data, dispatch, getState);
  }
};