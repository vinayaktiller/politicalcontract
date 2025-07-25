import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
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

export const fetchConversations = createAsyncThunk(
  'chatList/fetchConversations',
  async (force: boolean = false, { getState }) => {
    const state = getState() as RootState;
    if (!force && state.chatList.lastFetched && Date.now() - state.chatList.lastFetched < 300000) {
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
    messageReceived(state, action) {
      const { conversation_id, message, sender_id } = action.payload;
      const conversation = state.entities[conversation_id];
      
      if (conversation) {
        conversation.last_message = message;
        conversation.last_message_timestamp = new Date().toISOString();
        
        if (sender_id !== conversation.other_user.id) {
          conversation.unread_count += 1;
        }
      }
    },
    conversationRead(state, action) {
      const conversation = state.entities[action.payload];
      if (conversation) {
        conversation.unread_count = 0;
      }
    },
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

export const { messageReceived, conversationRead, resetChatList } = chatListSlice.actions;

export default chatListSlice.reducer;

// Selectors
export const selectAllConversations = (state: RootState) => 
  state.chatList.ids.map(id => state.chatList.entities[id]);

export const selectConversationById = (id: string) => (state: RootState) => 
  state.chatList.entities[id];