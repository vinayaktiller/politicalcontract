import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import api from '../../../../../api';
import { RootState } from '../../../../../store';

export interface CircleContact {
  id: number;
  name: string;
  profile_pic: string | null;
  relation: string;
}

interface CircleContactsState {
  contacts: CircleContact[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  lastFetched: number | null;
}

const initialState: CircleContactsState = {
  contacts: [],
  status: 'idle',
  error: null,
  lastFetched: null,
};

export const fetchCircleContacts = createAsyncThunk(
  'circleContacts/fetchCircleContacts',
  async (force: boolean = false, { getState, rejectWithValue }) => {
    const state = getState() as RootState;
    if (!force && state.circleContacts.lastFetched && Date.now() - state.circleContacts.lastFetched < 300000) {
      return null;
    }
    
    try {
      const response = await api.get<CircleContact[]>('/api/blog/circle-contacts/',);
      return response.data;
    } catch (error) {
      return rejectWithValue('Failed to fetch circle contacts');
    }
  }
);

const circleContactsSlice = createSlice({
  name: 'circleContacts',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCircleContacts.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchCircleContacts.fulfilled, (state, action) => {
        if (action.payload) {
          state.contacts = action.payload;
          state.lastFetched = Date.now();
        }
        state.status = 'succeeded';
      })
      .addCase(fetchCircleContacts.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string || 'Failed to fetch contacts';
      });
  },
});

export default circleContactsSlice.reducer;

export const selectCircleContacts = (state: RootState) => state.circleContacts.contacts;
export const selectCircleStatus = (state: RootState) => state.circleContacts.status;