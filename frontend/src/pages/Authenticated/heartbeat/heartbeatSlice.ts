import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../api';
import { format, isToday, isYesterday } from 'date-fns';

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
  // ✅ NEW: Track when data was last fetched
  lastFetched: string | null;
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
  lastFetched: null,
};

interface CheckUserActivityResponse {
  is_active_today: boolean;
  was_active_yesterday: boolean;
  streak_count: number;
}

// ✅ NEW: Helper function to check if data is stale
const shouldRefetchData = (lastFetched: string | null): boolean => {
  if (!lastFetched) return true;
  
  const lastFetchedDate = new Date(lastFetched);
  const now = new Date();
  
  // Refetch if:
  // 1. It's a new day (after midnight)
  // 2. Data was fetched more than 1 hour ago (safety net)
  // 3. Data was never fetched before
  return !isToday(lastFetchedDate) || 
         (now.getTime() - lastFetchedDate.getTime()) > 60 * 60 * 1000; // 1 hour
};

export const checkUserActivity = createAsyncThunk<
  CheckUserActivityResponse,
  number,
  { state: { heartbeat: HeartbeatState } }
>(
  'heartbeat/checkActivity',
  async (userId: number, { getState, rejectWithValue }) => {
    try {
      const state = getState().heartbeat;
      
      // ✅ Check if we need to refetch or can use cached data
      if (!shouldRefetchData(state.lastFetched)) {
        throw new Error('CACHE_VALID'); // Special signal to use cached data
      }
      
      const today = format(new Date(), 'yyyy-MM-dd');
      const response = await api.get(
        `/api/activity_reports/heartbeat/check-activity/`,
        { params: { user_id: userId, date: today } }
      );
      return response.data as CheckUserActivityResponse;
    } catch (err: any) {
      // If it's our cache valid signal, re-throw it so we can handle in extraReducers
      if (err.message === 'CACHE_VALID') {
        throw new Error('CACHE_VALID');
      }
      
      // Regular error handling
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
  number,
  { state: { heartbeat: HeartbeatState } }
>(
  'heartbeat/fetchActivityHistory',
  async (userId: number, { getState, rejectWithValue }) => {
    try {
      const state = getState().heartbeat;
      
      // ✅ Check if we need to refetch history
      if (!shouldRefetchData(state.lastFetched)) {
        throw new Error('CACHE_VALID'); // Special signal to use cached data
      }
      
      const response = await api.get(
        `/api/activity_reports/heartbeat/activity-history/`,
        { params: { user_id: userId } }
      );
      const data = response.data as { history: ActivityHistoryItem[] };
      return data.history;
    } catch (err: any) {
      if (err.message === 'CACHE_VALID') {
        throw new Error('CACHE_VALID');
      }
      
      const message = err.response?.data
        ? typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data)
        : 'Failed to fetch history';
      return rejectWithValue(message);
    }
  }
);

export const markUserActive = createAsyncThunk<
  string,
  number,
  { state: { heartbeat: HeartbeatState } }
>(
  'heartbeat/markActive',
  async (userId: number, { rejectWithValue, dispatch }) => {
    try {
      const today = format(new Date(), 'yyyy-MM-dd');
      await api.post('/api/activity_reports/heartbeat/mark-active/', {
        user_id: userId,
        date: today,
      });
      
      // Always refetch after marking active
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
    clearAllHeartbeatData: (state) => {
      return initialState;
    },
    // ✅ NEW: Manually invalidate cache to force refetch
    invalidateCache: (state) => {
      state.lastFetched = null;
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
          state.lastFetched = new Date().toISOString(); // ✅ Update fetch timestamp
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
        // ✅ Handle cache valid case - don't show error, keep existing data
        if (action.error.message === 'CACHE_VALID') {
          state.status = 'succeeded';
          state.error = null;
          // Keep existing data, just update the fetch timestamp
          state.lastFetched = new Date().toISOString();
        } else {
          state.status = 'failed';
          state.error = action.payload as string;
        }
      })
      .addCase(fetchActivityHistory.pending, (state) => {
        state.historyStatus = 'loading';
        state.historyError = null;
      })
      .addCase(fetchActivityHistory.fulfilled, (state, action) => {
        state.historyStatus = 'succeeded';
        state.activityHistory = action.payload;
        state.historyError = null;
        state.lastFetched = new Date().toISOString(); // ✅ Update fetch timestamp
      })
      .addCase(fetchActivityHistory.rejected, (state, action) => {
        // ✅ Handle cache valid case
        if (action.error.message === 'CACHE_VALID') {
          state.historyStatus = 'succeeded';
          state.historyError = null;
          state.lastFetched = new Date().toISOString();
        } else {
          state.historyStatus = 'failed';
          state.historyError = action.payload as string;
        }
      })
      .addCase(markUserActive.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(markUserActive.fulfilled, (state, action) => {
        state.lastActiveDate = action.payload;
        state.lastUpdated = format(new Date(), 'yyyy-MM-dd');
        state.lastFetched = new Date().toISOString(); // ✅ Update fetch timestamp
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
  clearAllHeartbeatData,
  invalidateCache // ✅ Export the new action
} = heartbeatSlice.actions;
export default heartbeatSlice.reducer;