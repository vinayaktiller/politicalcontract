// src/features/chat/chatList/chatListSlice.ts
import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../../api';
import { RootState } from '../../../../store';
import { ChatListState, Conversation } from './chatTypes';

const initialState: ChatListState = {
  entities: {},
  ids: [],
  status: 'idle',
  error: null,
  lastFetched: null,
};

// Async thunk for fetching conversations (with 5-minute cache)
export const fetchConversations = createAsyncThunk<
  Conversation[] | null,
  boolean | undefined,
  { state: RootState }
>(
  'chatList/fetchConversations',
  async (force = false, { getState }) => {
    const state = getState();
    if (
      !force &&
      state.chatList.lastFetched &&
      Date.now() - state.chatList.lastFetched < 300000 // 5 minutes cache
    ) {
      return null;
    }
    const response = await api.get<Conversation[]>('/api/chat/chatlist/');
    return response.data;
  }
);

const chatListSlice = createSlice({
  name: 'chatList',
  initialState,
  reducers: {
    // Update conversation fields and optionally move to top
    updateConversation: (
      state,
      action: PayloadAction<{
        id: string;
        changes: Partial<Conversation>;
        moveToTop?: boolean;
      }>
    ) => {
      const { id, changes, moveToTop } = action.payload;
      const conversation = state.entities[id];
      if (conversation) {
        Object.assign(conversation, changes);

        if (moveToTop) {
          state.ids = state.ids.filter(convId => convId !== id);
          state.ids.unshift(id);
        }
      }
    },

    // Reset unread count on conversation read
    conversationRead(state, action: PayloadAction<string>) {
      const conversation = state.entities[action.payload];
      if (conversation) {
        conversation.unread_count = 0;
      }
    },

    // Add a new conversation to entities and ids (at the top)
    addNewConversation(state, action: PayloadAction<Conversation>) {
      const conversation = action.payload;
      state.entities[conversation.id] = conversation;
      if (!state.ids.includes(conversation.id)) {
        state.ids.unshift(conversation.id);
      }
    },

    // Reset entire chat list state
    resetChatList: () => initialState,
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchConversations.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        if (action.payload) {
          action.payload.forEach((conversation) => {
            state.entities[conversation.id] = conversation;
            if (!state.ids.includes(conversation.id)) {
              state.ids.push(conversation.id);
            }
          });
          state.lastFetched = Date.now();
        }
        state.status = 'succeeded';
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch conversations';
      });
  },
});

export const {
  updateConversation,
  conversationRead,
  addNewConversation,
  resetChatList,
} = chatListSlice.actions;

export default chatListSlice.reducer;

// Selectors
export const selectAllConversations = (state: RootState): Conversation[] =>
  state.chatList.ids.map((id) => state.chatList.entities[id]);

export const selectConversationById = (id: string) => (state: RootState) =>
  state.chatList.entities[id];
