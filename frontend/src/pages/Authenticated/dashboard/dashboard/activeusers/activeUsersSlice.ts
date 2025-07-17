import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ActiveUsersState {
  activeCount: number; // From 'active_users' updates
  totalCount: number;  // From 'petitioners' updates
  activeLoading: boolean;
  totalLoading: boolean;
  activeError: string | null;
  totalError: string | null;
}

const initialState: ActiveUsersState = {
  activeCount: 0,
  totalCount: 0,
  activeLoading: true,
  totalLoading: true,
  activeError: null,
  totalError: null,
};

const activeUsersSlice = createSlice({
  name: 'activeUsers',
  initialState,
  reducers: {
    setActiveUsersCount: (state, action: PayloadAction<number>) => {
      state.activeCount = action.payload;
      state.activeLoading = false;
      state.activeError = null;
    },
    setTotalUsersCount: (state, action: PayloadAction<number>) => {
      state.totalCount = action.payload;
      state.totalLoading = false;
      state.totalError = null;
    },
    setActiveError: (state, action: PayloadAction<string>) => {
      state.activeLoading = false;
      state.activeError = action.payload;
    },
    setTotalError: (state, action: PayloadAction<string>) => {
      state.totalLoading = false;
      state.totalError = action.payload;
    },
    startActiveLoading: (state) => {
      state.activeLoading = true;
      state.activeError = null;
    },
    startTotalLoading: (state) => {
      state.totalLoading = true;
      state.totalError = null;
    },
  },
});

export const { 
  setActiveUsersCount, 
  setTotalUsersCount,
  setActiveError,
  setTotalError,
  startActiveLoading,
  startTotalLoading
} = activeUsersSlice.actions;

export default activeUsersSlice.reducer;