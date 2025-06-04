import { configureStore, combineReducers } from '@reduxjs/toolkit';
import storage from 'redux-persist/lib/storage';
import { persistReducer, persistStore, createTransform } from 'redux-persist';
import { PersistConfig } from 'redux-persist/es/types';
import userReducer from './login/login_logoutSlice';
import notificationsReducer from './pages/Authenticated/flowpages/notificationpages/notification_state/notificationsSlice';
import thunk from "redux-thunk";

// Define interfaces
interface UserState {
    isLoggedIn: boolean;
    user_email: string;
}

interface NotificationState {
    isConnected: boolean;
    socket: WebSocket | null;
    notifications: any[];
}

// Transform to remove WebSocket from state during persistence
const notificationTransform = createTransform(
    (inboundState: NotificationState) => ({
        ...inboundState,
        socket: null, // Remove WebSocket before persisting
    }),
    (outboundState: NotificationState) => outboundState,
    { whitelist: ['notifications'] }
);

// Combine reducers
const rootReducer = combineReducers({
    user: userReducer,
    notifications: notificationsReducer,
});

// Define RootState type for persist config
export type RootState = ReturnType<typeof rootReducer>;

// Define Persist Config
const persistConfig: PersistConfig<RootState> = {
    key: 'root',
    storage,
    whitelist: ['user', 'notifications'],
    transforms: [notificationTransform],
};

// Persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store with middleware to ignore specific non-serializable action/state paths
export const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware): ReturnType<typeof getDefaultMiddleware> =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: [
                    "persist/PERSIST",
                    "notifications/setSocket", // ✅ Ignore only this action
                ],
                ignoredPaths: [
                    "notifications.socket", // ✅ Ignore only this state path
                ],
            },
        }),
});

// Create the persistor
export const persistor = persistStore(store);

// Define RootState type for useSelector hooks
export type AppDispatch = typeof store.dispatch;
