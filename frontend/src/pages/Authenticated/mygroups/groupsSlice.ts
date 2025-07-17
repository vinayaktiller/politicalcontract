import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import api from '../../../api';

interface User {
  id: number;
  name: string;
  profilepic: string | null;
}

export interface Group {
  id: number;
  name: string;
  profile_pic: string | null;
  founder: User;
  speakers: User[];
  members_count: number;
  created_at: string;
  institution: string;
  links: string[];
  photos: string[];
}

interface GroupsData {
  upcoming_groups: Group[];
  old_groups: Group[];
}

interface GroupsState {
  groups: GroupsData | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: GroupsState = {
  groups: null,
  status: 'idle',
  error: null,
};

export const fetchGroups = createAsyncThunk('groups/fetchGroups', async () => {
  const response = await api.get<GroupsData>('/api/event/user-groups/');
  return response.data;
});

const groupsSlice = createSlice({
  name: 'groups',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchGroups.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchGroups.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.groups = action.payload;
      })
      .addCase(fetchGroups.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch groups';
      });
  },
});

export default groupsSlice.reducer;