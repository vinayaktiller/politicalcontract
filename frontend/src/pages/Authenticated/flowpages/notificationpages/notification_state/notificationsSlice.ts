import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Notification } from "./notificationsTypes";

interface NotificationsState {
  notifications: Notification[];
  socket: WebSocket | null;
  isConnected: boolean;
  nextId: number;
}

const initialState: NotificationsState = {
  notifications: [],
  socket: null,
  isConnected: false,
  nextId: 1,
};

const notificationsSlice = createSlice({
  name: "notifications",
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<Omit<Notification, 'id'>>) => {
      const newNotification = action.payload;
      
      // Check if notification already exists
      const existingIndex = state.notifications.findIndex(n => 
        n.notification_number === newNotification.notification_number &&
        n.notification_type === newNotification.notification_type
      );
      
      if (existingIndex !== -1) {
        // Update mutable fields of the existing notification
        const existing = state.notifications[existingIndex];
        existing.notification_message = newNotification.notification_message;
        existing.notification_data = newNotification.notification_data;
        existing.notification_number = newNotification.notification_number;
        existing.notification_freshness = newNotification.notification_freshness;
        if ('created_at' in newNotification && newNotification.created_at !== undefined) {
          (existing as any).created_at = newNotification.created_at;
        }
      } else {
        // Add new notification
        const notification = {
          ...newNotification,
          id: state.nextId,
        } as Notification;
        
        state.notifications.unshift(notification);
        state.nextId += 1;
        
        // Keep only the latest 50 notifications
        if (state.notifications.length > 50) {
          state.notifications.pop();
        }
      }
    },
    removeNotification: (state, action: PayloadAction<number>) => {
      state.notifications = state.notifications.filter(
        notification => notification.id !== action.payload
      );
    },
    removeNotificationByDetails: (
      state, 
      action: PayloadAction<{ notification_type: string; notification_number: string }>
    ) => {
      state.notifications = state.notifications.filter(
        notification => 
          !(notification.notification_type === action.payload.notification_type && 
            notification.notification_number === action.payload.notification_number)
      );
    },
    markAsViewed: (state, action: PayloadAction<number>) => {
      const notification = state.notifications.find(
        n => n.id === action.payload
      );
      if (notification) {
        notification.notification_freshness = true;
      }
    },
    setSocket: (state, action: PayloadAction<WebSocket | null>) => {
      state.socket = action.payload;
      state.isConnected = action.payload !== null;
    },
    setConnected: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    // NEW: Reset the entire notifications state to initial state
    resetNotifications: (state) => {
      state.notifications = [];
      state.socket = null;
      state.isConnected = false;
      state.nextId = 1;
    }
  },
});

export const { 
  addNotification, 
  setSocket, 
  setConnected,
  removeNotification,
  removeNotificationByDetails,
  markAsViewed,
  clearNotifications,
  resetNotifications // NEW: Export the new action
} = notificationsSlice.actions;

export default notificationsSlice.reducer;