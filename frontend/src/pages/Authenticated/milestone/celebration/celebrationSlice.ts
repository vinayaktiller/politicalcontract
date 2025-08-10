// src/store/celebrationSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { MilestoneNotificationData } from "../../../../pages/Authenticated/flowpages/notificationpages/notification_state/notificationsTypes";

export interface CelebrationData extends MilestoneNotificationData {
  id: number;
}

interface CelebrationState {
  isOpen: boolean;
  data: CelebrationData | null;
}

const initialState: CelebrationState = {
  isOpen: false,
  data: null,
};

const celebrationSlice = createSlice({
  name: "celebration",
  initialState,
  reducers: {
    triggerCelebration: (state, action: PayloadAction<CelebrationData>) => {
      state.isOpen = true;
      state.data = action.payload;
    },
    closeCelebration: (state) => {
      state.isOpen = false;
      state.data = null;
    },
  },
});

export const { triggerCelebration, closeCelebration } = celebrationSlice.actions;
export default celebrationSlice.reducer;