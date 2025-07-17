import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../api';
import { format, isToday, subDays, eachDayOfInterval } from 'date-fns';

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
      return rejectWithValue(err.response?.data || 'Failed to check activity');
    }
  }
);

export const fetchActivityHistory = createAsyncThunk<
  ActivityHistoryItem[],  // Changed to return array directly
  number
>(
  'heartbeat/fetchActivityHistory',
  async (userId: number, { rejectWithValue }) => {
    try {
      const response = await api.get(
        `/api/activity_reports/heartbeat/activity-history/`,
        { params: { user_id: userId } }
      );
      // Access history property from response
      const data = response.data as { history: ActivityHistoryItem[] };
      return data.history;
    } catch (err: any) {
      return rejectWithValue(err.response?.data || 'Failed to fetch history');
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
      return rejectWithValue(err.response?.data || 'Failed to mark active');
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
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(checkUserActivity.pending, (state) => {
        state.status = 'loading';
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
      })
      .addCase(fetchActivityHistory.fulfilled, (state, action) => {
        state.historyStatus = 'succeeded';
        // Store the history array directly
        state.activityHistory = action.payload;
      })
      .addCase(fetchActivityHistory.rejected, (state, action) => {
        state.historyStatus = 'failed';
        state.historyError = action.payload as string;
      })
      .addCase(markUserActive.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(markUserActive.fulfilled, (state, action) => {
        state.lastActiveDate = action.payload;
        state.lastUpdated = format(new Date(), 'yyyy-MM-dd');
      })
      .addCase(markUserActive.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { resetState, invalidateIfStale, resetForNewDay } = heartbeatSlice.actions;
export default heartbeatSlice.reducer;