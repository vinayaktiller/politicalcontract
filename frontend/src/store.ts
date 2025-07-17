// src/store/store.ts
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import storage from 'redux-persist/lib/storage';
import { persistReducer, persistStore, createTransform } from 'redux-persist';
import { PersistConfig } from 'redux-persist/es/types';
import userReducer from './login/login_logoutSlice';
import notificationsReducer from './pages/Authenticated/flowpages/notificationpages/notification_state/notificationsSlice';
import timelineReducer from './pages/Authenticated/Timelinepage/timelineSlice';
import heartbeatReducer, { initialState as initialHeartbeatState } from './pages/Authenticated/heartbeat/heartbeatSlice';
import activeUsersReducer from './pages/Authenticated/dashboard/dashboard/activeusers/activeUsersSlice';

// Interfaces
interface UserState {
  isLoggedIn: boolean;
  user_email: string;
}

interface NotificationState {
  isConnected: boolean;
  socket: WebSocket | null;
  notifications: any[];
}

// Strip WebSocket before saving
const notificationTransform = createTransform<NotificationState, NotificationState>(
  (inboundState) => ({ ...inboundState, socket: null }),
  (outboundState) => outboundState,
  { whitelist: ['notifications'] }
);

// Combine reducers
const rootReducer = combineReducers({
  user: userReducer,
  notifications: notificationsReducer,
  timeline: timelineReducer,
  heartbeat: heartbeatReducer,
  activeUsers: activeUsersReducer,
});

export type RootState = ReturnType<typeof rootReducer>;

const persistConfig: PersistConfig<RootState> = {
  key: 'root',
  storage,
  whitelist: ['user', 'notifications', 'timeline', 'heartbeat'],
  transforms: [notificationTransform],
  stateReconciler: (inboundState, originalState, reducedState) => {
    // Check if heartbeat data is stale (not from today)
    const today = new Date().toISOString().split('T')[0];
    if (inboundState.heartbeat?.lastUpdated !== today) {
      return {
        ...inboundState,
        heartbeat: {
          ...initialHeartbeatState,
          streak: inboundState.heartbeat?.streak || 0,
          status: 'idle'
        }
      };
    }
    return inboundState;
  },
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

// Store setup
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          'persist/PERSIST', 
          'notifications/setSocket',
          'heartbeat/checkActivity/fulfilled',
          'heartbeat/markActive/fulfilled',
          'activeUsers/setSocket'
        ],
        ignoredPaths: [
          'notifications.socket',
          'heartbeat.lastUpdated',
          'activeUsers.socket'
        ],
      },
    }),
});

export const persistor = persistStore(store);
export type AppDispatch = typeof store.dispatch;