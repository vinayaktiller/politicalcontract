// // src/store/activeUsersThunks.ts
// import { Dispatch } from '@reduxjs/toolkit';
// import { RootState } from '../../../../../store';
// import {
//   setActiveUsersCount,
//   setConnectionError,
//   setSocket,
//   closeConnection,
//   startLoading
// } from './activeUsersSlice';

// const RECONNECT_BASE_DELAY = 1000;
// let reconnectAttempts = 0;

// const getReconnectDelay = () => {
//   const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
//   return Math.min(delay, 30000); // Max 30 seconds
// };

// export const connectActiveUsersWebSocket = () => 
//   async (dispatch: Dispatch, getState: () => RootState) => {
//     // SAFER STATE ACCESS - FIX FOR UNDEFINED STATE
//     const state = getState();
//     const activeUsersState = state.activeUsers || {};
//     const socket = activeUsersState.socket || null;

//     // FIXED: Use explicit number comparisons instead of includes()
//     if (socket) {
//       const readyState = socket.readyState;
//       if (readyState === WebSocket.CONNECTING || readyState === WebSocket.OPEN) {
//         socket.close(4000, 'Reconnecting');
//       }
//     }

//     dispatch(startLoading());

//     const host = window.location.host;
//     const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
//     const wsUrl = `${protocol}//${host}/ws/activity/today/`;

//     try {
//       const newSocket = new WebSocket(wsUrl);
//       dispatch(setSocket(newSocket));

//       newSocket.onopen = () => {
//         reconnectAttempts = 0;
//         dispatch(setConnectionError(''));
//       };

//       newSocket.onmessage = (event) => {
//         try {
//           const data = JSON.parse(event.data);
//           if (typeof data.count === 'number') {
//             dispatch(setActiveUsersCount(data.count));
//           } else {
//             console.error('Invalid data format:', data);
//             dispatch(setConnectionError('Invalid data format'));
//           }
//         } catch (error) {
//           console.error('Error parsing message:', error, event.data);
//           dispatch(setConnectionError('Invalid data format'));
//         }
//       };

//       newSocket.onerror = (error) => {
//         console.error('WebSocket error:', error);
//       };

//       newSocket.onclose = (event) => {
//         if (event.code === 4000) return; // Intentional close
        
//         dispatch(setConnectionError('Connection closed'));
        
//         // Attempt reconnect
//         reconnectAttempts++;
//         const delay = getReconnectDelay();
//         setTimeout(() => {
//           dispatch(connectActiveUsersWebSocket() as any);
//         }, delay);
//       };
//     } catch (error) {
//       console.error('Connection failed:', error);
//       dispatch(setConnectionError('Connection failed'));
      
//       // Attempt reconnect
//       reconnectAttempts++;
//       const delay = getReconnectDelay();
//       setTimeout(() => dispatch(connectActiveUsersWebSocket() as any), delay);
//     }
//   };

// export const disconnectActiveUsersWebSocket = () => 
//   (dispatch: Dispatch, getState: () => RootState) => {
//     // SAFER STATE ACCESS - FIX FOR UNDEFINED STATE
//     const state = getState();
//     const activeUsersState = state.activeUsers || {};
//     const socket = activeUsersState.socket || null;
    
//     if (socket) {
//       socket.close(4000, 'User initiated disconnect');
//     }
//     dispatch(closeConnection());
//   };

export {}; // Add this line to make it a module