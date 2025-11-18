import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UserContextState {
  currentPage: string;
  isInChatRoom: boolean;
  activeChatRoomId: string | null;
}

const initialState: UserContextState = {
  currentPage: '/',
  isInChatRoom: false,
  activeChatRoomId: null,
};

const userContextSlice = createSlice({
  name: 'userContext',
  initialState,
  reducers: {
    setCurrentPage: (state, action: PayloadAction<string>) => {
      state.currentPage = action.payload;
      state.isInChatRoom = action.payload.startsWith('/chat/') && action.payload !== '/chat';
      state.activeChatRoomId = state.isInChatRoom ? action.payload.split('/').pop() || null : null;
    },
    setChatRoomState: (state, action: PayloadAction<{ isInChatRoom: boolean; roomId: string | null }>) => {
      state.isInChatRoom = action.payload.isInChatRoom;
      state.activeChatRoomId = action.payload.roomId;
    },
  },
});

export const { setCurrentPage, setChatRoomState } = userContextSlice.actions;
export default userContextSlice.reducer;