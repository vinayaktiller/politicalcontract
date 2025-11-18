import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../../api";
import {
  TimelineSliceState,
  TimelineState,
  TimelineHeadResponse,
  TimelineTailResponse,
} from "./timelineTypes";

const initialState: TimelineSliceState = {
  timelines: {},
  status: "idle",
  error: null,
};

export const fetchTimelineHead = createAsyncThunk<
  Partial<TimelineState>,
  { timelineNumber: number; timelineOwner: number },
  { state: { timeline: TimelineSliceState }; rejectValue: { timelineNumber: number; error: string } }
>(
  "timeline/fetchTimelineHead",
  async ({ timelineNumber, timelineOwner }, { getState, rejectWithValue }) => {
    const state = getState();
    const currentTimeline = state.timeline.timelines[timelineNumber];
    const rawNextPage = currentTimeline?.nextPage;

    console.log(`[fetchTimelineHead] Current nextPage: ${rawNextPage}`);

    // ✅ Stop fetching if all pages are already fetched
    if (rawNextPage === null) {
      console.log(`[fetchTimelineHead] Stopping fetch: all pages already fetched`);
      return rejectWithValue({ timelineNumber, error: "All pages fetched" });
    }

    // ✅ If nextPage is 0 (initial state), treat as page 1
    const page = rawNextPage === 0 ? 1 : rawNextPage || 1;

    console.log(`[fetchTimelineHead] Fetching page: ${page}`);

    try {
      const response = await api.get<TimelineHeadResponse>(
        `/api/users/timeline/${timelineOwner}/?page=${page}`
      );

      const isLastPage = response.data.next === null;

      console.log(`[fetchTimelineHead] Received data. Is last page? ${isLastPage}`);

      const data: Partial<TimelineState> & { timelineNumber: number } = {
        timelineNumber,
        timelineHead: response.data.results,
        nextPage: isLastPage ? null : page + 1,
        newload: response.data.load ?? 0,
        timelineHeadLength: response.data.count ?? 0,
      };

      if (page === 1 && response.data.user_profile) {
        data.timelineTail = [response.data.user_profile];
      }

      return data;
    } catch (err: any) {
      console.error(`[fetchTimelineHead] Error while fetching:`, err);
      return rejectWithValue({
        timelineNumber,
        error: err.response?.data || "An error occurred",
      });
    }
  }
);

export const fetchTimelineTail = createAsyncThunk(
  "timeline/fetchTimelineTail",
  async (
    { timelineNumber, profileId }: { timelineNumber: number; profileId: number },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.get<TimelineTailResponse>(
        `/api/users/timeline/tail/${profileId}/`
      );
      return { timelineNumber, data: response.data };
    } catch (error: any) {
      return rejectWithValue({
        timelineNumber,
        error: error.response?.data || "An error occurred",
      });
    }
  }
);

export const shiftTimelinePathThunk = createAsyncThunk(
  "timeline/shiftTimelinePathThunk",
  async (
    { timelineNumber, profileId, index }: { timelineNumber: number; profileId: number; index: number },
    { rejectWithValue }
  ) => {
    try {
      const response = await api.get<TimelineTailResponse>(
        `/api/users/timeline/tail/${profileId}/`
      );
      return { timelineNumber, data: response.data, index };
    } catch (error: any) {
      return rejectWithValue({
        timelineNumber,
        error: error.response?.data || "An error occurred",
      });
    }
  }
);

const timelineSlice = createSlice({
  name: "timeline",
  initialState,
  reducers: {
    addTimeline: (state, action) => {
      const { timelineNumber, timelineOwner } = action.payload;
      state.timelines[timelineNumber] = {
        timelineNumber,
        timelineOwner,
        timelineHead: [],
        timelineTail: [],
        nextPage: 0, // ✅ Initial state is 0 (fetch not yet started)
        timelineHeadLength: 0,
        newload: 0,
        scrollPosition: null,
      };
    },
    updateScrollPosition: (state, action) => {
      const { timelineNumber, position } = action.payload;
      if (state.timelines[timelineNumber]) {
        state.timelines[timelineNumber].scrollPosition = position;
      }
    },
    shiftTimelinePath: (state, action) => {
      const { timelineNumber, data, index } = action.payload;
      if (state.timelines[timelineNumber]) {
        const tail = state.timelines[timelineNumber].timelineTail;
        tail[index] = data;
        state.timelines[timelineNumber].timelineTail = tail.slice(0, index + 1);
      }
    },
    // ✅ NEW: Clear all timeline data explicitly
    clearAllTimelines: (state) => {
      state.timelines = {};
      state.status = "idle";
      state.error = null;
    },
    // ✅ NEW: Clear specific timeline
    clearTimeline: (state, action) => {
      const { timelineNumber } = action.payload;
      if (state.timelines[timelineNumber]) {
        delete state.timelines[timelineNumber];
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTimelineHead.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchTimelineHead.fulfilled, (state, action) => {
        const payload = action.payload;
        if (payload && payload.timelineNumber !== undefined) {
          const timeline = state.timelines[payload.timelineNumber];
          if (timeline) {
            timeline.timelineHead = [
              ...timeline.timelineHead,
              ...(payload.timelineHead || []),
            ];
            timeline.nextPage = payload.nextPage !== undefined ? payload.nextPage : null;
            timeline.timelineHeadLength = payload.timelineHeadLength ?? 0;
            timeline.newload = payload.newload ?? 0;

            if (payload.timelineTail) {
              timeline.timelineTail = payload.timelineTail;
            }

            console.log(`[Reducer] Updated nextPage: ${timeline.nextPage}`);
          }
        }
        state.status = "succeeded";
      })
      .addCase(fetchTimelineHead.rejected, (state, action) => {
        state.status = "failed";
        const payload = action.payload as { timelineNumber: number; error: string };
        if (payload && state.timelines[payload.timelineNumber]) {
          state.timelines[payload.timelineNumber].error = payload.error;
          console.log(`[Reducer] Rejected fetch for timeline ${payload.timelineNumber}: ${payload.error}`);
        }
      })
      .addCase(fetchTimelineTail.fulfilled, (state, action) => {
        const { timelineNumber, data } = action.payload;
        const timeline = state.timelines[timelineNumber];
        if (timeline) {
          timeline.timelineTail.push(data);
        }
      })
      .addCase(shiftTimelinePathThunk.fulfilled, (state, action) => {
        const { timelineNumber, data, index } = action.payload;
        const timeline = state.timelines[timelineNumber];
        if (timeline) {
          timeline.timelineTail[index] = data;
          timeline.timelineTail = timeline.timelineTail.slice(0, index + 1);
        }
      })
      .addCase(fetchTimelineTail.rejected, (state, action) => {
        const payload = action.payload as { timelineNumber: number; error: string };
        if (payload && state.timelines[payload.timelineNumber]) {
          state.timelines[payload.timelineNumber].error = payload.error;
        }
      });
  },
});

export const {
  addTimeline,
  updateScrollPosition,
  shiftTimelinePath,
  clearAllTimelines, // ✅ Export the new action
  clearTimeline,     // ✅ Export the new action
} = timelineSlice.actions;

export default timelineSlice.reducer;