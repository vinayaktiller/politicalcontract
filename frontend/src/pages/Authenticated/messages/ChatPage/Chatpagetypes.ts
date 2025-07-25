import { Middleware } from '@reduxjs/toolkit';
import { RootState } from '../../../../store';

const CHAT_STORAGE_KEY = 'chatState';

export interface MessageSender {
  id: string;
  name: string;
  profile_pic: string | null;
}

export interface Message {
  id: string;
  content: string;
  timestamp: string;
  read: boolean;
  sender_name: string;
  sender_profile: string | null;
  is_own: boolean;
}

export interface UserProfile {
  id: string;
  name: string;
  profile_pic: string | null;
}

export interface ConversationDetail {
  id: string;
  other_user: UserProfile;
}

export interface ChatRoomState {
  conversation: ConversationDetail | null;
  messages: Message[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  sendStatus: 'idle' | 'sending' | 'succeeded' | 'failed';
  sendError: string | null;
  lastReadTime: string | null;
  initialized: boolean;
}

export interface ChatState {
  rooms: {
    [conversationId: string]: ChatRoomState;
  };
  currentRoomId: string | null;
}

// ✅ Selectors with null safety
export const selectCurrentRoom = (state: RootState) => {
  if (!state.chat) return null;
  const currentRoomId = state.chat.currentRoomId;
  if (!currentRoomId) return null;
  return state.chat.rooms[currentRoomId] || null;
};

export const selectConversation = (state: RootState) =>
  selectCurrentRoom(state)?.conversation || null;

export const selectMessages = (state: RootState) =>
  selectCurrentRoom(state)?.messages || [];

export const selectChatStatus = (state: RootState) =>
  selectCurrentRoom(state)?.status || 'idle';

export const selectSendStatus = (state: RootState) =>
  selectCurrentRoom(state)?.sendStatus || 'idle';

export const selectChatError = (state: RootState) =>
  selectCurrentRoom(state)?.error || null;

export const selectRoomInitialized = (state: RootState, conversationId: string) =>
  state.chat?.rooms[conversationId]?.initialized || false;

// ✅ Persistence logic
export function loadChatState(): ChatState | undefined {
  try {
    const serializedState = localStorage.getItem(CHAT_STORAGE_KEY);
    if (serializedState === null) return undefined;
    const state = JSON.parse(serializedState) as ChatState;

    // Reset status flags to avoid stale UI
    const rooms = Object.entries(state.rooms).reduce((acc, [id, room]) => {
      acc[id] = {
        ...room,
        status: 'idle',
        error: null,
        sendStatus: 'idle',
        sendError: null,
      };
      return acc;
    }, {} as Record<string, ChatRoomState>);

    return {
      ...state,
      rooms,
    };
  } catch (e) {
    console.error('Failed to load chat state', e);
    return undefined;
  }
}

export function saveChatState(state: ChatState) {
  try {
    const serializedState = JSON.stringify(state);
    localStorage.setItem(CHAT_STORAGE_KEY, serializedState);
  } catch (e) {
    console.error('Failed to save chat state', e);
  }
}

// ✅ Type-safe middleware
export const chatPersistenceMiddleware: Middleware<{}, RootState> =
  (store) => (next) => (action) => {
    const result = next(action);

    // Type-safe access to action.type
    if (
      typeof action === 'object' &&
      action !== null &&
      'type' in action &&
      typeof action.type === 'string' &&
      action.type.startsWith('chat/')
    ) {
      saveChatState(store.getState().chat);
    }

    return result;
  };
