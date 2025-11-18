// import { createSlice, PayloadAction } from "@reduxjs/toolkit";

// interface NotificationData {
//   gmail: string;
//   first_name: string;
//   last_name: string;
//   profile_picture: string;
//   date_of_birth: string;
//   gender: string;
//   country: number;
//   state: number;
//   district: number;
//   subdistrict: number;
//   village: number;
//   event_type: string;
//   event_id: number;
//   initiator_id: number;
//   is_online: boolean;
// }

// export interface Notification {
//   id: number;
//   notification_type: string;
//   notification_message: string;
//   notification_data: NotificationData;
//   notification_number: number;
//   notification_freshness: boolean;
//   created_at?: string;
// }

// interface NotificationsState {
//   notifications: Notification[];
//   socket: WebSocket | null;
//   isConnected: boolean;
//   nextId: number;
// }

// const initialState: NotificationsState = {
//   notifications: [],
//   socket: null,
//   isConnected: false,
//   nextId: 1,
// };

// const notificationsSlice = createSlice({
//   name: "notifications",
//   initialState,
//   reducers: {
//     addNotification: (state, action: PayloadAction<Omit<Notification, 'id'>>) => {
//       const notification = {
//         ...action.payload,
//         id: state.nextId,
//       };
      
//       const exists = state.notifications.some(n => 
//         n.notification_number === notification.notification_number &&
//         n.notification_data.gmail === notification.notification_data.gmail
//       );
      
//       if (!exists) {
//         state.notifications.unshift(notification);
//         state.nextId += 1;
//         if (state.notifications.length > 50) {
//           state.notifications.pop();
//         }
//       }
//     },
//     removeNotification(state, action: PayloadAction<number>) {
//       state.notifications = state.notifications.filter(
//         (notification) => notification.id !== action.payload
//       );
//     },
//     markAsViewed(state, action: PayloadAction<number>) {
//       const notification = state.notifications.find(
//         (n) => n.id === action.payload
//       );
//       if (notification) {
//         notification.notification_freshness = true;
//       }
//     },
//     setSocket(state, action: PayloadAction<WebSocket | null>) {
//       state.socket = action.payload;
//       state.isConnected = action.payload !== null;
//     },
//     setConnected(state, action: PayloadAction<boolean>) {
//       state.isConnected = action.payload;
//     },
//     clearNotifications(state) {
//       state.notifications = [];
//     }
//   },
// });

// export const { 
//   addNotification, 
//   setSocket, 
//   setConnected,
//   removeNotification,
//   markAsViewed,
//   clearNotifications
// } = notificationsSlice.actions;

// export default notificationsSlice.reducer;

// notificationsSlice.ts
// notificationsSlice.ts


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
  clearNotifications
} = notificationsSlice.actions;

export default notificationsSlice.reducer;