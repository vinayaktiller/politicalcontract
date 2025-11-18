import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../api';
import { format, isToday } from 'date-fns';

interface ActivityHistoryItem {
  date: string;
  active: boolean;
}

interface HeartbeatState {
  heartState: 'inactive' | 'passive' | 'active' | 'hyperactive';
  streak: number;
  lastActiveDate: string | null;
  lastUpdated: string | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  activityHistory: ActivityHistoryItem[];
  historyStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
  historyError: string | null;
}

export const initialState: HeartbeatState = {
  heartState: 'inactive',
  streak: 0,
  lastActiveDate: null,
  lastUpdated: null,
  status: 'idle',
  error: null,
  activityHistory: [],
  historyStatus: 'idle',
  historyError: null,
};

interface CheckUserActivityResponse {
  is_active_today: boolean;
  was_active_yesterday: boolean;
  streak_count: number;
}

export const checkUserActivity = createAsyncThunk<
  CheckUserActivityResponse,
  number
>(
  'heartbeat/checkActivity',
  async (userId: number, { rejectWithValue }) => {
    try {
      const today = format(new Date(), 'yyyy-MM-dd');
      const response = await api.get(
        `/api/activity_reports/heartbeat/check-activity/`,
        { params: { user_id: userId, date: today } }
      );
      return response.data as CheckUserActivityResponse;
    } catch (err: any) {
      // Ensure error message is a string
      const message = err.response?.data
        ? typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data)
        : 'Failed to check activity';
      return rejectWithValue(message);
    }
  }
);

export const fetchActivityHistory = createAsyncThunk<
  ActivityHistoryItem[],
  number
>(
  'heartbeat/fetchActivityHistory',
  async (userId: number, { rejectWithValue }) => {
    try {
      const response = await api.get(
        `/api/activity_reports/heartbeat/activity-history/`,
        { params: { user_id: userId } }
      );
      const data = response.data as { history: ActivityHistoryItem[] };
      return data.history;
    } catch (err: any) {
      const message = err.response?.data
        ? typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data)
        : 'Failed to fetch history';
      return rejectWithValue(message);
    }
  }
);

export const markUserActive = createAsyncThunk(
  'heartbeat/markActive',
  async (userId: number, { rejectWithValue, dispatch }) => {
    try {
      const today = format(new Date(), 'yyyy-MM-dd');
      await api.post('/api/activity_reports/heartbeat/mark-active/', {
        user_id: userId,
        date: today,
      });
      
      // Refetch updated status after marking active
      await dispatch(checkUserActivity(userId));
      await dispatch(fetchActivityHistory(userId));
      return today;
    } catch (err: any) {
      const message = err.response?.data
        ? typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data)
        : 'Failed to mark active';
      return rejectWithValue(message);
    }
  }
);

const heartbeatSlice = createSlice({
  name: 'heartbeat',
  initialState,
  reducers: {
    resetState: () => initialState,
    invalidateIfStale: (state) => {
      if (state.lastUpdated && !isToday(new Date(state.lastUpdated))) {
        return initialState;
      }
    },
    resetForNewDay: (state) => {
      return {
        ...initialState,
        streak: state.streak,
        status: 'idle',
        historyStatus: state.historyStatus,
        activityHistory: state.activityHistory,
      };
    },
    // ✅ NEW: Clear all heartbeat data explicitly
    clearAllHeartbeatData: (state) => {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(checkUserActivity.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(
        checkUserActivity.fulfilled,
        (
          state,
          action: PayloadAction<{
            is_active_today: boolean;
            was_active_yesterday: boolean;
            streak_count: number;
          }>
        ) => {
          const { is_active_today, was_active_yesterday, streak_count } = action.payload;
          
          state.status = 'succeeded';
          state.streak = streak_count;
          state.lastUpdated = format(new Date(), 'yyyy-MM-dd');
          state.error = null;
          
          if (is_active_today) {
            state.heartState = streak_count >= 5 ? 'hyperactive' : 'active';
            state.lastActiveDate = format(new Date(), 'yyyy-MM-dd');
          } else if (was_active_yesterday) {
            state.heartState = 'passive';
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            state.lastActiveDate = format(yesterday, 'yyyy-MM-dd');
          } else {
            state.heartState = 'inactive';
            state.lastActiveDate = null;
          }
        }
      )
      .addCase(checkUserActivity.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      })
      .addCase(fetchActivityHistory.pending, (state) => {
        state.historyStatus = 'loading';
        state.historyError = null;
      })
      .addCase(fetchActivityHistory.fulfilled, (state, action) => {
        state.historyStatus = 'succeeded';
        state.activityHistory = action.payload;
        state.historyError = null;
      })
      .addCase(fetchActivityHistory.rejected, (state, action) => {
        state.historyStatus = 'failed';
        state.historyError = action.payload as string;
      })
      .addCase(markUserActive.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(markUserActive.fulfilled, (state, action) => {
        state.lastActiveDate = action.payload;
        state.lastUpdated = format(new Date(), 'yyyy-MM-dd');
        state.error = null;
      })
      .addCase(markUserActive.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { 
  resetState, 
  invalidateIfStale, 
  resetForNewDay,
  clearAllHeartbeatData // ✅ Export the new action
} = heartbeatSlice.actions;
export default heartbeatSlice.reducer;