// src/features/chat/contacts/contactsSlice.ts
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import api from '../../../../../api'; 
import { RootState } from '../../../../../store';

export interface Contact {
  id: number;
  name: string;
  profile_pic?: string;
  has_conversation: boolean;
  conversation_id: string | null;
}

export interface ContactsState {
  contacts: Contact[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  lastFetched: number | null;
}

const initialState: ContactsState = {
  contacts: [],
  status: 'idle',
  error: null,
  lastFetched: null,
};

export const fetchContacts = createAsyncThunk(
  'contacts/fetchContacts',
  async (force: boolean = false, { getState, rejectWithValue }) => {
    const state = getState() as RootState;
    if (!force && state.contacts.lastFetched && Date.now() - state.contacts.lastFetched < 300000) {
      return null;
    }
    try {
      const response = await api.get<Contact[]>('/api/chat/contacts/');
      return response.data;
    } catch (error) {
      return rejectWithValue('Failed to fetch contacts');
    }
  }
);

const contactsSlice = createSlice({
  name: 'contacts',
  initialState,
  reducers: {
    resetContacts: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchContacts.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchContacts.fulfilled, (state, action) => {
        if (action.payload) {
          state.contacts = action.payload;
          state.lastFetched = Date.now();
        }
        state.status = 'succeeded';
      })
      .addCase(fetchContacts.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string || 'Failed to fetch contacts';
      });
  },
});

export const { resetContacts } = contactsSlice.actions;
export default contactsSlice.reducer;

export const selectContacts = (state: RootState) => state.contacts.contacts;
export const selectContactsStatus = (state: RootState) => state.contacts.status;