import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../../api';

interface ActivityHistoryItem {
  date: string;
  active: boolean;
}

interface NetworkUser {
  id: number;
  name: string;
  profile_pic: string | null;
  connection_type: string;
  is_active_today: boolean;
  streak_count: number;
  activity_history: ActivityHistoryItem[];
}

interface ActivityUpdate {
  user_id: number;
  is_active_today: boolean;
  streak_count: number;
}

export interface HeartbeatNetworkState {
  networkUsers: NetworkUser[];
  currentUserId: number | null;
  today: string | null;
  status: 'idle' | 'loading' | 'refreshing' | 'succeeded' | 'failed';
  error: string | null;
}

interface NetworkActivityResponse {
  network_users: NetworkUser[];
  current_user_id: number;
  today: string;
  update_type: 'full' | 'activity_updates' | 'no_changes';
  activity_updates?: ActivityUpdate[];
}

interface RefreshNetworkActivityParams {
  activeIds: string;
  inactiveIds: string;
}

export const initialState: HeartbeatNetworkState = {
  networkUsers: [],
  currentUserId: null,
  today: null,
  status: 'idle',
  error: null,
};

export const fetchNetworkActivity = createAsyncThunk<
  NetworkActivityResponse,
  void,
  { rejectValue: string }
>(
  'heartbeatNetwork/fetchNetworkActivity',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get(
        `/api/activity_reports/heartbeat/network/`
      );
      return response.data as NetworkActivityResponse;
    } catch (err: any) {
      const message = err.response?.data
        ? typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data)
        : 'Failed to fetch network activity';
      return rejectWithValue(message);
    }
  }
);

export const refreshNetworkActivity = createAsyncThunk<
  NetworkActivityResponse,
  RefreshNetworkActivityParams,
  { rejectValue: string }
>(
  'heartbeatNetwork/refreshNetworkActivity',
  async ({ activeIds, inactiveIds }, { rejectWithValue }) => {
    try {
      const response = await api.get(
        `/api/activity_reports/heartbeat/network/`,
        {
          params: {
            active_ids: activeIds,
            inactive_ids: inactiveIds
          }
        }
      );
      return response.data as NetworkActivityResponse;
    } catch (err: any) {
      const message = err.response?.data
        ? typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data)
        : 'Failed to refresh network activity';
      return rejectWithValue(message);
    }
  }
);

const heartbeatNetworkSlice = createSlice({
  name: 'heartbeatNetwork',
  initialState,
  reducers: {
    clearNetworkData: (state) => {
      state.networkUsers = [];
      state.currentUserId = null;
      state.today = null;
      state.status = 'idle';
      state.error = null;
    },
    resetNetworkStatus: (state) => {
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Network Activity (initial load)
      .addCase(fetchNetworkActivity.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchNetworkActivity.fulfilled, (state, action: PayloadAction<NetworkActivityResponse>) => {
        state.status = 'succeeded';
        state.networkUsers = action.payload.network_users;
        state.currentUserId = action.payload.current_user_id;
        state.today = action.payload.today;
        state.error = null;
      })
      .addCase(fetchNetworkActivity.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Unknown error occurred';
      })
      
      // Refresh Network Activity (subsequent loads)
      .addCase(refreshNetworkActivity.pending, (state) => {
        state.status = 'refreshing';
        state.error = null;
      })
      .addCase(refreshNetworkActivity.fulfilled, (state, action: PayloadAction<NetworkActivityResponse>) => {
        state.status = 'succeeded';
        
        if (action.payload.update_type === 'full') {
          // Replace all data (new users detected)
          state.networkUsers = action.payload.network_users;
        } else if (action.payload.update_type === 'activity_updates' && action.payload.activity_updates) {
          // Update activity status for existing users
          action.payload.activity_updates.forEach(update => {
            const user = state.networkUsers.find(u => u.id === update.user_id);
            if (user) {
              user.is_active_today = update.is_active_today;
              user.streak_count = update.streak_count;
            }
          });
        }
        // For 'no_changes', do nothing
        
        state.currentUserId = action.payload.current_user_id;
        state.today = action.payload.today;
        state.error = null;
      })
      .addCase(refreshNetworkActivity.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Unknown error occurred';
      });
  },
});

export const { clearNetworkData, resetNetworkStatus } = heartbeatNetworkSlice.actions;
export default heartbeatNetworkSlice.reducer;