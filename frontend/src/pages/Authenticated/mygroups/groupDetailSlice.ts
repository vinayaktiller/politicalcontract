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

interface GroupDetailState {
  group: Group | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: GroupDetailState = {
  group: null,
  status: 'idle',
  error: null,
};

export const fetchGroup = createAsyncThunk(
  'groupDetail/fetchGroup',
  async (groupId: string) => {
    const response = await api.get<Group>(`/api/groups/${groupId}/`);
    return response.data;
  }
);

const groupDetailSlice = createSlice({
  name: 'groupDetail',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchGroup.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchGroup.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.group = action.payload;
      })
      .addCase(fetchGroup.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message || 'Failed to fetch group details';
      });
  },
});

export default groupDetailSlice.reducer;