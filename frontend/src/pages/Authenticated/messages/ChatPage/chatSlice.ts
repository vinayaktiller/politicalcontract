import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../../api';
import { RootState } from '../../../../store';
import { 
  ChatRoomState, 
  ChatState, 
  Message, 
  ConversationDetail,
  selectRoomInitialized,
  loadChatState,
  chatPersistenceMiddleware 
} from './Chatpagetypes';



const initialRoomState: ChatRoomState = {
  conversation: null,
  messages: [],
  status: 'idle',
  error: null,
  sendStatus: 'idle',
  sendError: null,
  lastReadTime: null,
  initialized: false,
};

const initialState: ChatState = loadChatState() || {
  rooms: {},
  currentRoomId: null,
};

// Helper to get or initialize room state
const getRoomState = (state: ChatState, conversationId: string) => {
  if (!state.rooms[conversationId]) {
    state.rooms[conversationId] = { ...initialRoomState };
  }
  return state.rooms[conversationId];
};

// Thunks
export const fetchConversation = createAsyncThunk(
  'chat/fetchConversation',
  async (conversationId: string, { getState, rejectWithValue }) => {
    try {
      const response = await api.get<ConversationDetail>(`/api/chat/conversations/${conversationId}/`);
      return { conversationId, data: response.data };
    } catch (error: any) {
      return rejectWithValue({ 
        conversationId, 
        error: error.response?.data?.error || 'Failed to fetch conversation' 
      });
    }
  }
);

export const fetchMessages = createAsyncThunk(
  'chat/fetchMessages',
  async (conversationId: string, { getState, rejectWithValue }) => {
    try {
      const response = await api.get<Message[]>(`/api/chat/chat/${conversationId}/messages/`);
      return { conversationId, data: response.data };
    } catch (error: any) {
      return rejectWithValue({ 
        conversationId, 
        error: error.response?.data?.error || 'Failed to fetch messages' 
      });
    }
  }
);

export const initializeRoom = createAsyncThunk(
  'chat/initializeRoom',
  async (conversationId: string, { dispatch, getState }) => {
    const state = getState() as RootState;
    const roomInitialized = selectRoomInitialized(state, conversationId);
    
    if (!roomInitialized) {
      await dispatch(fetchConversation(conversationId));
      await dispatch(fetchMessages(conversationId));
    }
    
    return conversationId;
  }
);

export const sendNewMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ conversationId, content }: { conversationId: string; content: string }, 
  { rejectWithValue, getState }) => {
    try {
      const response = await api.post<Message>(`/api/chat/chat/${conversationId}/send/`, { content });
      return { conversationId, data: response.data };
    } catch (error: any) {
      return rejectWithValue({
        conversationId,
        error: error.response?.data?.error || 'Failed to send message'
      });
    }
  }
);

export const markMessagesRead = createAsyncThunk(
  'chat/markMessagesRead',
  async (conversationId: string, { rejectWithValue, getState }) => {
    try {
      const state = getState() as RootState;
      
      // Add safety checks for state.chat
      if (!state.chat) {
        return { conversationId, lastReadTime: null };
      }
      
      const room = state.chat.rooms[conversationId];
      
      // If room doesn't exist, return early
      if (!room) {
        return { conversationId, lastReadTime: null };
      }
      
      const hasNewMessages = room.messages.some(
        msg => !msg.is_own && !msg.read
      );
      
      if (hasNewMessages) {
        await api.post(`/api/chat/chat/${conversationId}/mark_read/`);
        return { conversationId, lastReadTime: new Date().toISOString() };
      }
      
      return { conversationId, lastReadTime: room.lastReadTime };
    } catch (error: any) {
      return rejectWithValue({
        conversationId,
        error: error.response?.data?.error || 'Failed to mark messages as read'
      });
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setCurrentRoom: (state, action: PayloadAction<string>) => {
      state.currentRoomId = action.payload;
    },
    resetRoomState: (state, action: PayloadAction<string>) => {
      const conversationId = action.payload;
      if (state.rooms[conversationId]) {
        state.rooms[conversationId] = { ...initialRoomState };
      }
    },
    addMessage: (state, action: PayloadAction<{ conversationId: string; message: Message }>) => {
      const { conversationId, message } = action.payload;
      const room = getRoomState(state, conversationId);
      
      // Only add if not already present
      if (!room.messages.some(m => m.id === message.id)) {
        room.messages.push(message);
      }
    },
    removeMessage: (state, action: PayloadAction<{ conversationId: string; messageId: string }>) => {
      const { conversationId, messageId } = action.payload;
      const room = state.rooms[conversationId];
      
      if (room) {
        room.messages = room.messages.filter(msg => msg.id !== messageId);
      }
    },
    updateMessage: (
      state, 
      action: PayloadAction<{ 
        conversationId: string; 
        messageId: string; 
        changes: Partial<Message> 
      }>
    ) => {
      const { conversationId, messageId, changes } = action.payload;
      const room = state.rooms[conversationId];
      
      if (room) {
        const index = room.messages.findIndex(msg => msg.id === messageId);
        if (index !== -1) {
          room.messages[index] = { ...room.messages[index], ...changes };
        }
      }
    },
    markMessagesOptimistic: (
      state, 
      action: PayloadAction<{ conversationId: string; lastReadTime: string }>
    ) => {
      const { conversationId, lastReadTime } = action.payload;
      const room = state.rooms[conversationId];
      
      if (room) {
        room.lastReadTime = lastReadTime;
        room.messages = room.messages.map(msg => ({
          ...msg,
          read: msg.is_own ? msg.read : true
        }));
      }
    }
  },
  extraReducers: (builder) => {
    builder
      // Initialize Room
      .addCase(initializeRoom.fulfilled, (state, action) => {
        const conversationId = action.payload;
        state.currentRoomId = conversationId;
      })
      
      // Fetch Conversation
      .addCase(fetchConversation.pending, (state, action) => {
        const conversationId = action.meta.arg;
        const room = getRoomState(state, conversationId);
        room.status = 'loading';
        room.error = null;
      })
      .addCase(fetchConversation.fulfilled, (state, action) => {
        const { conversationId, data } = action.payload;
        const room = getRoomState(state, conversationId);
        room.status = 'succeeded';
        room.conversation = data;
      })
      .addCase(fetchConversation.rejected, (state, action) => {
        const payload = action.payload as { conversationId: string; error: string };
        const room = getRoomState(state, payload.conversationId);
        room.status = 'failed';
        room.error = payload.error;
      })
      
      // Fetch Messages
      .addCase(fetchMessages.pending, (state, action) => {
        const conversationId = action.meta.arg;
        const room = getRoomState(state, conversationId);
        room.status = 'loading';
        room.error = null;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        const { conversationId, data } = action.payload;
        const room = getRoomState(state, conversationId);
        room.status = 'succeeded';
        room.messages = data;
        room.initialized = true;
        
        if (!room.lastReadTime) {
          room.lastReadTime = new Date().toISOString();
        }
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        const payload = action.payload as { conversationId: string; error: string };
        const room = getRoomState(state, payload.conversationId);
        room.status = 'failed';
        room.error = payload.error;
      })
      
      // Send Message
      .addCase(sendNewMessage.pending, (state, action) => {
        const { conversationId } = action.meta.arg;
        const room = getRoomState(state, conversationId);
        room.sendStatus = 'sending';
        room.sendError = null;
      })
      .addCase(sendNewMessage.fulfilled, (state, action) => {
        const { conversationId, data } = action.payload;
        const room = getRoomState(state, conversationId);
        room.sendStatus = 'succeeded';
        
        // Replace temporary message
        const realMessage = data;
        const tempIndex = room.messages.findIndex(msg => 
          msg.id.startsWith('temp-') && 
          msg.content === realMessage.content
        );
        
        if (tempIndex !== -1) {
          room.messages[tempIndex] = realMessage;
        } else {
          room.messages.push(realMessage);
        }
      })
      .addCase(sendNewMessage.rejected, (state, action) => {
        const payload = action.payload as { conversationId: string; error: string };
        const room = getRoomState(state, payload.conversationId);
        room.sendStatus = 'failed';
        room.sendError = payload.error;
        
        // Remove temporary message
        const tempIndex = room.messages.findIndex(msg => msg.id.startsWith('temp-'));
        if (tempIndex !== -1) {
          room.messages.splice(tempIndex, 1);
        }
      })
      
      // Mark Messages Read
      .addCase(markMessagesRead.fulfilled, (state, action) => {
        const { conversationId, lastReadTime } = action.payload;
        const room = state.rooms[conversationId];
        
        if (room && lastReadTime) {
          room.lastReadTime = lastReadTime;
          room.messages = room.messages.map(msg => ({
            ...msg,
            read: msg.is_own ? msg.read : true
          }));
        }
      });
  }
});

export const { 
  setCurrentRoom, 
  resetRoomState, 
  addMessage, 
  removeMessage, 
  updateMessage,
  markMessagesOptimistic
} = chatSlice.actions;

export default chatSlice.reducer;
export { chatPersistenceMiddleware };