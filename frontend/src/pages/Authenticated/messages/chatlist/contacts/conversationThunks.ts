// import { createAsyncThunk } from '@reduxjs/toolkit';
// import api from '../../../../../api';
// import { AppDispatch, RootState } from '../../../../../store';

// import { setCurrentRoom, addMessage, updateMessage } from '../../ChatPage/chatSlice';
// import { updateConversation } from '../../../messages/chatlist/chatListSlice';
// import { Message } from '../../ChatPage/Chatpagetypes';
// import { Conversation } from '../../../messages/chatlist/chatTypes';
// import { UserProfile } from '../../ChatPage/Chatpagetypes';


// // Helper to find conversation by contact ID
// const findConversationByContactId = (state: RootState, contactId: number): string | null => {
//   const allConversations = Object.values(state.chatList.entities);
//   const currentUserId = state.auth.user?.id;
  
//   return allConversations.find(conversation => 
//     (conversation?.participant1.id === currentUserId && conversation?.participant2.id === contactId) ||
//     (conversation?.participant2.id === currentUserId && conversation?.participant1.id === contactId)
//   )?.id || null;
// };

// export const startNewConversation = createAsyncThunk(
//   'conversations/startNew',
//   async (contactId: number, { dispatch, getState }) => {
//     const state = getState() as RootState;
    
//     // 1. Check if conversation already exists locally
//     const existingConversationId = findConversationByContactId(state, contactId);
//     if (existingConversationId) {
//       dispatch(setCurrentRoom(existingConversationId));
//       return existingConversationId;
//     }

//     try {
//       // 2. Create new conversation on server
//       const response = await api.post(`/api/chat/conversation/start/${contactId}/`);
//       const conversationId = response.data.conversation_id as string;
      
//       // 3. Create optimistic message in chat slice
//       const currentUser = state.auth.user!;
//       const contact = state.contacts.contacts.find(c => c.id === contactId);
      
//       if (contact) {
//         const optimisticMessage: Message = {
//           id: `temp-${Date.now()}`,
//           content: 'Conversation started',
//           sender: currentUser.id,
//           is_own: true,
//           timestamp: new Date().toISOString(),
//           status: 'sending',
//           conversation: conversationId
//         };
        
//         dispatch(addMessage({
//           conversationId,
//           message: optimisticMessage
//         }));
        
//         // 4. Update conversation in chat list
//         const newConversation: Conversation = {
//           id: conversationId,
//           participant1: {
//             id: currentUser.id,
//             username: currentUser.username,
//             first_name: currentUser.first_name,
//             last_name: currentUser.last_name,
//             profile_pic: currentUser.profile_pic
//           },
//           participant2: {
//             id: contactId,
//             username: contact.name,
//             first_name: contact.name.split(' ')[0],
//             last_name: contact.name.split(' ')[1] || '',
//             profile_pic: contact.profile_pic || ''
//           },
//           last_message: optimisticMessage,
//           unread_count: 0,
//           updated_at: new Date().toISOString()
//         };
        
//         dispatch(updateConversation({
//           id: conversationId,
//           changes: newConversation,
//           moveToTop: true
//         }));
//       }
      
//       // 5. Set as current room
//       dispatch(setCurrentRoom(conversationId));
      
//       return conversationId;
//     } catch (error) {
//       console.error('Failed to start conversation:', error);
//       throw new Error('Failed to start conversation');
//     }
//   }
// );

// // Handle message send response
// export const handleMessageSendResponse = createAsyncThunk(
//   'conversations/handleMessageResponse',
//   async ({ tempId, message }: { tempId: string; message: Message }, { dispatch }) => {
//     // Update message in chat slice
//     dispatch(updateMessage({
//       conversationId: message.conversation,
//       messageId: tempId,
//       changes: message
//     }));
    
//     // Update conversation in chat list
//     dispatch(updateConversation({
//       id: message.conversation,
//       changes: {
//         last_message: message,
//         updated_at: new Date().toISOString()
//       },
//       moveToTop: true
//     }));
//   }
// );
export {}