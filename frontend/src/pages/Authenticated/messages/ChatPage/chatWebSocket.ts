// import { Dispatch } from '@reduxjs/toolkit';
// import { RootState } from '../../../../store';
// import { addMessage, markMessagesOptimistic, removeMessage, updateMessage } from './chatSlice';
// import { Message } from './Chatpagetypes';

// const RECONNECT_BASE_DELAY = 1000;
// let reconnectAttempts = 0;
// let socket: WebSocket | null = null;

// const getReconnectDelay = () => {
//   const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
//   return Math.min(delay, 30000);
// };

// export const connectChatWebSocket = (
//   conversationId: string,
//   userId: string
// ) => async (dispatch: Dispatch, getState: () => RootState) => {
//   if (socket) {
//     socket.close(4000, 'New connection attempt');
//   }

//   try {
//     const authToken = localStorage.getItem('access_token');
//     const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
//     const host = window.location.host;
//     const wsUrl = `ws://localhost:8000/ws/chat/${conversationId}/?token=${authToken}`;
    
//     socket = new WebSocket(wsUrl);

//     socket.onopen = () => {
//       reconnectAttempts = 0;
//       console.log('Chat WebSocket connected');
//     };

//     socket.onmessage = (event: MessageEvent) => {
//       try {
//         const data = JSON.parse(event.data);
//         console.log('Received WebSocket message:', data);

//         // Handle message ACK (only for sender)
//         if (data.type === 'message_ack') {
//           const realMessage = data;
//           const state = getState();
          
//           // Find matching temp message
//           const now = new Date();
//           const twoSecondsAgo = new Date(now.getTime() - 2000);
//           const tempMessage = state.chat.messages.find(msg => 
//             msg.id.startsWith('temp-') && 
//             msg.content === realMessage.content &&
//             new Date(msg.timestamp) >= twoSecondsAgo
//           );

//           if (tempMessage) {
//             dispatch(updateMessage({
//               id: tempMessage.id,
//               changes: {
//                 id: realMessage.id,
//                 timestamp: realMessage.timestamp,
//                 read: realMessage.read,
//                 sender: realMessage.sender
//               }
//             }));
//           }
//           return;
//         }

//         // Chat message handling
//         if (data.type === 'chat_message') {
//           const messageData = data;

//           let profilePic = messageData.sender?.profile_pic;
//           if (profilePic && !profilePic.startsWith('http')) {
//             profilePic = `${window.location.origin}${profilePic}`;
//           }

//           const message: Message = {
//             id: messageData.id,
//             content: messageData.content,
//             timestamp: messageData.timestamp,
//             read: messageData.read || false,
//             sender_name: messageData.sender?.name || 'Unknown',
//             sender_profile: profilePic,
//             is_own: messageData.sender?.id === userId
//           };

//           dispatch(addMessage(message));
//         }

//         // Read receipt from other user
//         else if (data.type === 'read_receipt' && data.user_id !== userId) {
//           dispatch(markMessagesOptimistic(data.timestamp));
//         }

//         // Optimistic UI sync from server
//         else if (data.type === 'message_read_update') {
//           dispatch(markMessagesOptimistic(data.timestamp));
//         }

//       } catch (error) {
//         console.error('Message parsing error:', error);
//       }
//     };

//     socket.onclose = (event: CloseEvent) => {
//       switch (event.code) {
//         case 4000:
//         case 4001:
//           return;
//         default:
//           reconnectAttempts++;
//           const delay = getReconnectDelay();
//           console.log(`Reconnecting in ${delay / 1000} seconds...`);
//           setTimeout(() => {
//             if (conversationId && userId) {
//               dispatch(connectChatWebSocket(conversationId, userId) as any);
//             }
//           }, delay);
//       }
//     };

//     socket.onerror = (error: Event) => {
//       console.error('Chat WebSocket error:', error);
//       if (socket) socket.close();
//     };

//   } catch (error) {
//     console.error('Connection failed:', error);
//     const delay = getReconnectDelay();
//     setTimeout(() => {
//       if (conversationId && userId) {
//         dispatch(connectChatWebSocket(conversationId, userId) as any);
//       }
//     }, delay);
//   }
// };

// export const disconnectChatWebSocket = () => {
//   if (socket) {
//     socket.close(4000, 'User initiated disconnect');
//     socket = null;
//   }
// };

// export const sendChatMessage = (
//   conversationId: string,
//   content: string
// ) => {
//   if (socket && socket.readyState === WebSocket.OPEN) {
//     const message = JSON.stringify({
//       type: 'chat_message',
//       content
//     });
//     socket.send(message);
//     return true;
//   } else {
//     console.error('Chat WebSocket is not connected');
//     return false;
//   }
// };

// export const sendReadReceipt = () => {
//   if (socket && socket.readyState === WebSocket.OPEN) {
//     const message = JSON.stringify({
//       type: 'read_receipt'
//     });
//     socket.send(message);
//     return true;
//   }
//   return false;
// };

export {};
