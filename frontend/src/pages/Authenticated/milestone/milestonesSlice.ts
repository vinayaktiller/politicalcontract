// // src/features/milestones/milestoneSlice.ts
// import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
// import api from '../../../api';

// export interface Milestone {
//   milestone_id: string;
//   id: number;
//   user_id: number;
//   title: string;
//   text: string;
//   created_at: string;
//   delivered: boolean;
//   photo_id: number | null;
//   photo_url: string | null;
//   type: string | null;
// }

// interface MilestonesState {
//   milestones: Milestone[];
//   status: 'idle' | 'loading' | 'succeeded' | 'failed';
//   error: string | null;
//   lastUpdated: string | null;
// }

// const initialState: MilestonesState = {
//   milestones: [],
//   status: 'idle',
//   error: null,
//   lastUpdated: null,
// };

// export const fetchUserMilestones = createAsyncThunk<Milestone[], number>(
//   'milestones/fetchUserMilestones',
//   async (userId: number, { rejectWithValue }) => {
//     try {
//       const response = await api.get<Milestone[]>(
//         '/api/users/milestones/',
//         { params: { user_id: userId } }
//       );
//       console.log("loading milestones");
//       return response.data;
//     } catch (err: any) {
//       return rejectWithValue(err.response?.data || 'Failed to fetch milestones');
//     }
//   }
// );

// const milestonesSlice = createSlice({
//   name: 'milestones',
//   initialState,
//   reducers: {
//     resetMilestones: () => initialState,
//     invalidateMilestoneCache: (state) => {
//       if (state.lastUpdated && !isToday(new Date(state.lastUpdated))) {
//         // Mutate state properties directly instead of returning new object
//         state.milestones = [];
//         state.status = 'idle';
//         state.error = null;
//         state.lastUpdated = null;
//       }
//     },
//     // Modified: Add milestone with duplicate title check
//     addMilestone: (state, action: PayloadAction<Milestone>) => {
//       const newMilestone = action.payload;
//       console.log('Attempting to add milestone:', newMilestone);
//       const exists = state.milestones.some(m => m.title === newMilestone.title);
//       console.log('Milestone exists by title:', exists);
//       if (!exists) {
//         state.milestones.unshift(newMilestone);
//         state.lastUpdated = new Date().toISOString();
//       } else {
//         console.log('Skipped adding duplicate milestone by title:', newMilestone.title);
//       }
//     }
//   },
//   extraReducers: (builder) => {
//     builder
//       .addCase(fetchUserMilestones.pending, (state) => {
//         state.status = 'loading';
//       })
//       .addCase(fetchUserMilestones.fulfilled, (state, action: PayloadAction<Milestone[]>) => {
//         state.status = 'succeeded';
//         state.milestones = action.payload;
//         state.lastUpdated = new Date().toISOString();
//       })
//       .addCase(fetchUserMilestones.rejected, (state, action) => {
//         state.status = 'failed';
//         state.error = action.payload as string;
//       });
//   },
// });

// // Helper function (same as in heartbeat)
// function isToday(date: Date): boolean {
//   const today = new Date();
//   return date.getDate() === today.getDate() &&
//          date.getMonth() === today.getMonth() &&
//          date.getFullYear() === today.getFullYear();
// }

// // Export actions and reducer
// export const { resetMilestones, invalidateMilestoneCache, addMilestone } = milestonesSlice.actions;
// export default milestonesSlice.reducer;


// src/features/milestones/milestoneSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../../api';

export interface Milestone {
  milestone_id: string;
  id: number;
  user_id: number;
  title: string;
  text: string;
  created_at: string;
  delivered: boolean;
  photo_id: number | null;
  photo_url: string | null;
  type: string | null;
}

interface MilestonesState {
  milestones: Milestone[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  lastUpdated: string | null;
}

const initialState: MilestonesState = {
  milestones: [],
  status: 'idle',
  error: null,
  lastUpdated: null,
};

export const fetchUserMilestones = createAsyncThunk<Milestone[], number>(
  'milestones/fetchUserMilestones',
  async (userId: number, { rejectWithValue }) => {
    try {
      const response = await api.get<Milestone[]>(
        '/api/users/milestones/',
        { params: { user_id: userId } }
      );
      return response.data;
    } catch (err: any) {
      const message = err.response?.data 
        ? (typeof err.response.data === 'string' 
          ? err.response.data 
          : JSON.stringify(err.response.data)) 
        : 'Failed to fetch milestones';
      return rejectWithValue(message);
    }
  }
);

const milestonesSlice = createSlice({
  name: 'milestones',
  initialState,
  reducers: {
    resetMilestones: () => initialState,
    invalidateMilestoneCache: (state) => {
      if (state.lastUpdated && !isToday(new Date(state.lastUpdated))) {
        state.milestones = [];
        state.status = 'idle';
        state.error = null;
        state.lastUpdated = null;
      }
    },
    addMilestone: (state, action: PayloadAction<Milestone>) => {
      // Ensure milestones is an array before using .some()
      if (!Array.isArray(state.milestones)) {
        state.milestones = [];
      }

      const newMilestone = action.payload;

      // Defensive check: Confirm newMilestone has required id and title fields
      if (!newMilestone || typeof newMilestone.title !== 'string') {
        // Invalid milestone payload, do nothing or log error
        console.warn('Invalid milestone payload passed to addMilestone', newMilestone);
        return;
      }

      // Check if a milestone with the same title already exists
      const exists = state.milestones.some(m => m.title === newMilestone.title);

      // Add new milestone if it does not exist already
      if (!exists) {
        state.milestones.unshift(newMilestone);
        state.lastUpdated = new Date().toISOString();
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUserMilestones.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchUserMilestones.fulfilled, (state, action: PayloadAction<Milestone[]>) => {
        state.status = 'succeeded';
        state.milestones = action.payload;
        state.lastUpdated = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchUserMilestones.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

function isToday(date: Date): boolean {
  const today = new Date();
  return date.getDate() === today.getDate() &&
         date.getMonth() === today.getMonth() &&
         date.getFullYear() === today.getFullYear();
}

export const { resetMilestones, invalidateMilestoneCache, addMilestone } = milestonesSlice.actions;
export default milestonesSlice.reducer;
