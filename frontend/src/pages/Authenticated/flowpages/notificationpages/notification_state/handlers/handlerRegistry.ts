// handlers/handlerRegistry.ts

// -------------------------------
// IMPORTS – must always stay at top
// -------------------------------
import { Dispatch } from '@reduxjs/toolkit';
import { AppDispatch, RootState } from '../../../../../../store';

// Import all handlers
import {
  handleBlogUpload,
  handleBlogShared,
  handleBlogUnshared,
  handleBlogModified
} from './blogHandlers';

import {
  handleCommentUpdateMessage,
  handleCommentLikeUpdateMessage,
  handleReplyUpdateMessage
} from './commentHandlers';

import { handleBlogUpdateMessage } from './blogUpdateHandlers';

import {
  handleNotificationMessage,
  handleChatSystemMessage,
  handleGenericNotification
} from './chatHandlers';

// -------------------------------
// TYPES
// -------------------------------
export type MessageHandler = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => void;

export interface HandlerRegistry {
  [key: string]: MessageHandler;
}

// -------------------------------
// HANDLER REGISTRY FACTORY
// -------------------------------
export const createHandlerRegistry = (): HandlerRegistry => ({
  // Blog-related handlers
  blog_created: handleBlogUpload,
  blog_shared: handleBlogShared,
  blog_unshared: handleBlogUnshared,
  blog_modified: handleBlogModified,
  blog_update: handleBlogUpdateMessage,

  // Comment-related handlers
  comment_update: handleCommentUpdateMessage,
  comment_like_update: handleCommentLikeUpdateMessage,
  reply_update: handleReplyUpdateMessage,

  // Chat / Notification handlers
  notification_message: handleNotificationMessage,
  chat_system: handleChatSystemMessage,
  generic_notification: handleGenericNotification,
});

// -------------------------------
// MAIN MESSAGE ROUTER
// -------------------------------
export const handleWebSocketMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState,
  handlers: HandlerRegistry
): void => {
  const messageType = determineMessageType(data);

  if (handlers[messageType]) {
    handlers[messageType](data, dispatch, getState);
  } else {
    console.warn(`No handler for message type: ${messageType}`, data);
  }
};

// -------------------------------
// DETERMINE MESSAGE TYPE
// -------------------------------
const determineMessageType = (data: any): string => {
  // Handle notification_message with chat_system category (old compatibility)
  if (data?.type === 'notification_message' && data?.category === 'chat_system') {
    return 'chat_system';
  }

  if (data?.type) return data.type;
  if (data?.category === 'chat_system') return 'chat_system';

  if (data?.notification?.notification_type === 'Milestone_Notification') {
    return 'milestone_notification';
  }

  if (data?.notification) return 'generic_notification';

  return 'unknown';
};
