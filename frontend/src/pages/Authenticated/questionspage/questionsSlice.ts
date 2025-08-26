// questionsSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../api';

interface Question {
  id: number;
  text: string;
  author_id: number | null;
  is_approved: boolean;
  rank: number;
  activity_score: number;
  created_at: string;
}

interface QuestionsState {
  questions: Question[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  pagination: {
    currentPage: number;
    totalPages: number;
    totalCount: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

const initialState: QuestionsState = {
  questions: [],
  status: 'idle',
  error: null,
  pagination: {
    currentPage: 1,
    totalPages: 1,
    totalCount: 0,
    hasNext: false,
    hasPrevious: false,
  },
};

interface QuestionsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Question[];
}

export const fetchQuestions = createAsyncThunk<
  QuestionsResponse,
  { page?: number; pageSize?: number }
>(
  'questions/fetchQuestions',
  async ({ page = 1, pageSize = 5 }, { rejectWithValue }) => {
    try {
      const response = await api.get(
        `/api/blog_related/questions/`,
        { params: { page, page_size: pageSize } }
      );
      return response.data as QuestionsResponse;
    } catch (err: any) {
      return rejectWithValue(err.response?.data || 'Failed to fetch questions');
    }
  }
);

const questionsSlice = createSlice({
  name: 'questions',
  initialState,
  reducers: {
    resetQuestions: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchQuestions.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchQuestions.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.questions = action.payload.results;
        state.pagination = {
          currentPage: action.payload.next 
            ? parseInt(new URL(action.payload.next).searchParams.get('page') || '1') - 1
            : action.payload.previous 
              ? parseInt(new URL(action.payload.previous).searchParams.get('page') || '1') + 1
              : 1,
          totalPages: Math.ceil(action.payload.count / 5), // Assuming pageSize = 5
          totalCount: action.payload.count,
          hasNext: !!action.payload.next,
          hasPrevious: !!action.payload.previous,
        };
      })
      .addCase(fetchQuestions.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { resetQuestions } = questionsSlice.actions;
export default questionsSlice.reducer;