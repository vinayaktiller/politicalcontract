import { Dispatch } from '@reduxjs/toolkit';
import { AppDispatch, RootState } from '../../../../../store';
import {
  addNotification,
  removeNotificationByDetails,
  setConnected,
  setSocket,
} from './notificationsSlice';
import { addMessage, updateMessage } from '../../../messages/ChatPage/chatSlice';
import { updateConversation } from '../../../messages/chatlist/chatListSlice';
import { fetchUserMilestones } from '../../../milestone/milestonesSlice';
import { updateBlog, addComment, addBlog, addSharedBlog, removeSharedBlog } from '../../../blogrelated/blogpage/blogSlice';
import { MessageNotification } from './notificationsTypes';

// === Helper functions for comment tree ===

const findCommentInTree = (comments: any[], commentId: string): any => {
  for (const comment of comments) {
    if (comment.id === commentId) return comment;
    if (comment.replies && comment.replies.length > 0) {
      const found = findCommentInTree(comment.replies, commentId);
      if (found) return found;
    }
  }
  return null;
};

const updateCommentInTree = (comments: any[], commentId: string, updates: any): any[] => {
  return comments.map(comment => {
    if (comment.id === commentId) {
      return { ...comment, ...updates };
    }
    if (comment.replies && comment.replies.length > 0) {
      return {
        ...comment,
        replies: updateCommentInTree(comment.replies, commentId, updates)
      };
    }
    return comment;
  });
};

const addReplyToCommentInTree = (comments: any[], commentId: string, reply: any): any[] => {
  return comments.map(comment => {
    if (comment.id === commentId) {
      return {
        ...comment,
        replies: [...(comment.replies || []), reply]
      };
    }
    if (comment.replies && comment.replies.length > 0) {
      return {
        ...comment,
        replies: addReplyToCommentInTree(comment.replies, commentId, reply)
      };
    }
    return comment;
  });
};

const findBlogById = (state: RootState, blogId: string) => {
  for (const blogType of Object.keys(state.blog.blogs)) {
    const blog = state.blog.blogs[blogType].blogs.find(b => b.id === blogId);
    if (blog) return { blogType, blog };
  }
  return { blogType: null, blog: null };
};

// === Comment Handlers ===

const handleCommentUpdateMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, action, comment, user_id } = data;
  const blogType = 'circle';
  const state = getState();
  const blogsState = state.blog?.blogs?.[blogType];
  if (!blogsState || !Array.isArray(blogsState.blogs)) return;
  const blog = blogsState.blogs.find((b: any) => String(b.id) === String(blog_id));
  if (!blog) return;
  if (action === 'comment_added') {
    dispatch(
      addComment({
        blogType,
        blogId: String(blog_id),
        comment: comment,
      })
    );
  } else if (action === 'comment_deleted') {
    const updatedComments = blog.comments.filter((c: any) => c.id !== comment.id);
    dispatch(
      updateBlog({
        blogType,
        id: String(blog_id),
        updates: {
          comments: updatedComments,
          footer: {
            ...blog.footer,
            comments: blog.footer.comments.filter((id: string) => id !== comment.id),
          },
        },
      })
    );
  }
};

const handleCommentLikeUpdateMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, comment_id, action, likes_count, user_id } = data;
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);
  if (user_id === currentUserId) return;
  const { blogType, blog } = findBlogById(getState(), blog_id);
  if (!blogType || !blog) return;
  const updatedComments = updateCommentInTree(
    blog.comments, 
    comment_id, 
    { 
      likes: Array(likes_count).fill(0),
      has_liked: action === 'added'
    }
  );
  dispatch(
    updateBlog({
      blogType,
      id: blog_id,
      updates: {
        comments: updatedComments
      }
    })
  );
};

// === Blog Update Handlers ===

const handleBlogUpdateMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, update_type, action, user_id } = data;
  
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);
  
  if (user_id === currentUserId) return;
  const blogType = 'circle';
  const state = getState();
  const blogsState = state.blog?.blogs?.[blogType];
  if (!blogsState || !Array.isArray(blogsState.blogs)) return;
  const blog = blogsState.blogs.find((b: any) => String(b.id) === String(blog_id));
  if (!blog) return;
  const prevFooter = blog.footer || {
    likes: [] as number[],
    shares: [] as number[],
    relevant_count: [] as number[],
    irrelevant_count: [] as number[],
    comments: [] as string[],
    has_liked: false,
    has_shared: false,
  };
  const isLike = update_type === 'like';
  const targetKey: 'likes' | 'shares' = isLike ? 'likes' : 'shares';
  const actingUserId = typeof user_id === 'string' ? parseInt(user_id, 10) || user_id : user_id;
  const updatedArray = Array.isArray(prevFooter[targetKey])
    ? [...prevFooter[targetKey]]
    : [];
  if (action === 'added') {
    if (!updatedArray.some((id) => String(id) === String(actingUserId))) {
      updatedArray.push(actingUserId as any);
    }
  } else {
    const idx = updatedArray.findIndex((id) => String(id) === String(actingUserId));
    if (idx !== -1) {
      updatedArray.splice(idx, 1);
    }
  }
  const footerUpdates = {
    ...prevFooter,
    [targetKey]: updatedArray,
  };
  dispatch(
    updateBlog({
      blogType,
      id: String(blog_id),
      updates: {
        footer: footerUpdates,
      },
    })
  );
};

// === Reply Handler ===

const handleReplyUpdateMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, comment_id, reply, user_id } = data;
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);
  if (user_id === currentUserId) return;
  const { blogType, blog } = findBlogById(getState(), blog_id);
  if (!blogType || !blog) return;
  const updatedComments = addReplyToCommentInTree(
    blog.comments,
    comment_id,
    reply
  );
  dispatch(
    updateBlog({
      blogType,
      id: blog_id,
      updates: {
        comments: updatedComments,
        footer: {
          ...blog.footer,
          comments: [...blog.footer.comments, reply.id]
        }
      }
    })
  );
};

// === Blog Creation Handler ===

const handleBlogUpload = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, action, blog, user_id } = data;
  const blog_type = data.blog_type;
  console.log('Blog upload received:', blog_type);
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  if (user_id === currentUserId) return;

  if (action === 'blog_created' && blog && blog_type) {
    console.log('New blog received via WebSocket:', blog, blog_type);
    
    // Add to the 'circle' blog type since that's where the feed is stored
    dispatch(addBlog({ blogType: 'circle', blog }));
    
    // Also add to the specific blog type if it exists
    const state = getState();
    if (state.blog.blogs[blog_type]) {
      dispatch(addBlog({ blogType: blog_type, blog }));
    }
  }
};

// === Blog Share Handler ===

const handleBlogShared = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, action, blog, shared_by_user_id, original_author_id, user_id } = data;
  console.log('Blog share received:', blog_id, 'shared by:', shared_by_user_id);
  
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  // Don't process if it's our own share action
  if (user_id === currentUserId) {
    console.log('Ignoring own blog share action');
    return;
  }

  if (action === 'shared' && blog && shared_by_user_id && original_author_id) {
    console.log('Processing shared blog:', blog_id, 'shared by:', shared_by_user_id);
    
    // Use the addSharedBlog action to add the blog with share metadata
    dispatch(addSharedBlog({
      blogType: 'circle',
      blog: blog,
      sharedByUserId: shared_by_user_id,
      originalAuthorId: original_author_id
    }));
    
    console.log('Added shared blog to store:', blog_id);
  } else {
    console.error('Invalid share data received:', { 
      blog_id, 
      blog: !!blog, 
      shared_by_user_id, 
      original_author_id,
      action 
    });
  }
};

// === Blog Unshare Handler ===

const handleBlogUnshared = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, action, shared_by_user_id, original_author_id, user_id } = data;
  console.log('Blog unshare received:', blog_id, 'unshared by:', shared_by_user_id);
  
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  // Don't process if it's our own unshare action
  if (user_id === currentUserId) {
    console.log('Ignoring own blog unshare action');
    return;
  }

  if (action === 'unshared' && shared_by_user_id && original_author_id) {
    console.log('Processing unshared blog:', blog_id, 'unshared by:', shared_by_user_id);
    
    // Use the removeSharedBlog action to remove the shared blog
    dispatch(removeSharedBlog({
      blogType: 'circle',
      blogId: blog_id,
      sharedByUserId: shared_by_user_id
    }));
    
    console.log('Removed shared blog from store:', blog_id);
  } else {
    console.error('Invalid unshare data received:', { 
      blog_id, 
      shared_by_user_id, 
      original_author_id,
      action 
    });
  }
};

// === Blog Modification Handler ===

const handleBlogModified = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const { blog_id, blog, user_id } = data;
  const blog_type = data.blog_type;
  console.log('Blog modification received:', blog_type, blog_id);
  const currentUserId = parseInt(localStorage.getItem('user_id') || '0', 10);

  if (user_id === currentUserId) {
    console.log('Ignoring own blog modification');
    return;
  }

  if (blog && blog_type) {
    console.log('Processing modified blog:', blog_id, 'of type:', blog_type);
    
    // Update the blog in all relevant blog types
    const state = getState();
    
    // Update in 'circle' blog type
    if (state.blog.blogs['circle']) {
      dispatch(updateBlog({ blogType: 'circle', id: blog_id, updates: blog }));
      console.log('Updated blog in circle feed:', blog_id);
    } else {
      console.log('Circle blog type not found in state');
    }
    
    // Update in the specific blog type if it exists
    if (state.blog.blogs[blog_type]) {
      dispatch(updateBlog({ blogType: blog_type, id: blog_id, updates: blog }));
      console.log('Updated blog in specific type:', blog_type, blog_id);
    } else {
      console.log('Blog type not found in state:', blog_type);
    }
  } else {
    console.error('Invalid blog data received:', { blog_id, blog, blog_type });
  }
};

// === Message Notification Handler ===

const handleMessageNotification = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const state = getState();
  const currentRoomId = state.chat.currentRoomId;
  const conversationId = data.conversation_id;
  
  // Don't show notification if user is in this specific chat room
  if (currentRoomId === conversationId) {
    return;
  }

  // Check if we already have a message notification
  const existingMessageNotification = state.notifications.notifications.find(
    n => n.notification_type === 'Message_Notification'
  ) as MessageNotification | undefined;

  const chatListState = state.chatList;
  const totalUnreadCount = chatListState.ids.reduce((count, id) => {
    const conv = chatListState.entities[id];
    return count + (conv?.unread_count || 0);
  }, 0);

  const conversationCount = chatListState.ids.filter(id => {
    const conv = chatListState.entities[id];
    return conv && conv.unread_count > 0;
  }).length;

  if (existingMessageNotification) {
    // Update existing notification
    const updatedNotification: Omit<MessageNotification, 'id'> = {
      notification_type: "Message_Notification",
      notification_message: `You have ${totalUnreadCount} new messages from ${conversationCount} conversations`,
      notification_data: {
        conversation_id: conversationId,
        sender_id: data.sender_id,
        sender_name: data.sender_name,
        message_content: data.content,
        message_count: totalUnreadCount,
        conversation_count: conversationCount,
        timestamp: data.timestamp,
        profile_picture: data.sender_profile || null
      },
      notification_number: existingMessageNotification.notification_number,
      notification_freshness: false
    };

    // Remove old and add updated one to maintain order
    dispatch(removeNotificationByDetails({
      notification_type: "Message_Notification",
      notification_number: existingMessageNotification.notification_number,
    }));
    
    dispatch(addNotification(updatedNotification));
  } else {
    // Create new notification
    const messageNotification: Omit<MessageNotification, 'id'> = {
      notification_type: "Message_Notification",
      notification_message: `You have ${totalUnreadCount} new messages from ${conversationCount} conversations`,
      notification_data: {
        conversation_id: conversationId,
        sender_id: data.sender_id,
        sender_name: data.sender_name,
        message_content: data.content,
        message_count: totalUnreadCount,
        conversation_count: conversationCount,
        timestamp: data.timestamp,
        profile_picture: data.sender_profile || null
      },
      notification_number: `message_${Date.now()}`,
      notification_freshness: false
    };
    
    dispatch(addNotification(messageNotification));
  }
};

// === Chat System Handler ===

const handleChatSystemMessage = (
  data: any,
  dispatch: Dispatch,
  getState: () => RootState
) => {
  const subtype = data.subtype;
  const conversationId = data.conversation_id;
  const messageId = data.message_id;
  const status = data.status;

  switch (subtype) {
    case 'new_message': {
      const state = getState();
      const conversation = state.chat.rooms[conversationId]?.conversation;
      const room = state.chat.rooms[conversationId];
      const isCurrentRoom = state.chat.currentRoomId === conversationId;

      // Deduplication: ignore if message ID already exists
      if (room && room.messages.some((m) => m.id === messageId)) {
        console.log(`Duplicate new_message ignored for messageID: ${messageId}`);
        break;
      }

      let sender_name = 'Unknown';
      let sender_profile = null;
      if (conversation) {
        if (conversation.other_user.id === data.sender_id) {
          sender_name = conversation.other_user.name;
          sender_profile = conversation.other_user.profile_pic;
        }
      }

      const message = {
        id: messageId,
        content: data.content,
        timestamp: data.timestamp,
        status: data.status || 'sent',
        sender_name: data.sender_name || sender_name,
        sender_profile: data.sender_profile || sender_profile,
        is_own: false,
      };

      dispatch(addMessage({ conversationId, message }));

      // Update chat list conversation info
      const currentUnreadCount = state.chatList.entities[conversationId]?.unread_count || 0;
      dispatch(
        updateConversation({
          id: conversationId,
          changes: {
            last_message: data.content,
            last_message_timestamp: data.timestamp,
            unread_count: isCurrentRoom ? currentUnreadCount : currentUnreadCount + 1,
          },
          moveToTop: true,
        })
      );

      // Trigger message notification if not in current chat room
      if (!isCurrentRoom) {
        handleMessageNotification(data, dispatch, getState);
      }
      break;
    }

    case 'message_delivered':
    case 'delivered_update':
    case 'message_read':
    case 'read_update':
    case 'message_read_update':
      dispatch(
        updateMessage({
          conversationId,
          messageId,
          changes: { status },
        })
      );
      break;

    case 'message_sent':
      dispatch(
        updateMessage({
          conversationId,
          messageId: data.temp_id,
          changes: {
            id: data.message_id,
            status: data.status || 'sent',
            timestamp: data.timestamp,
          },
        })
      );
      break;

    default:
      console.warn('Unhandled chat subtype:', subtype);
  }
};

// === WebSocket Connection Thunk ===

const RECONNECT_BASE_DELAY = 1000;
let reconnectAttempts = 0;

const getReconnectDelay = () => {
  const delay = RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttempts);
  return Math.min(delay, 30000);
};

export const connectWebSocket =
  (userId: string) => async (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();

    // Avoid duplicate connections
    if (notifications.socket instanceof WebSocket) {
      const socket = notifications.socket;
      if (socket.readyState === WebSocket.CONNECTING) {
        socket.close(4000, 'New connection attempt');
        return;
      }
      if (socket.readyState === WebSocket.OPEN) {
        return;
      }
    }

    try {
      const authToken = localStorage.getItem('access_token');
      console.log('WebSocket connecting...' + authToken);
      const socket = new WebSocket(
        // `ws://localhost:8000/ws/notifications/${userId}/?token=${authToken}`
         `wss://pfs-be-01-buf0fwgnfgbechdu.centralus-01.azurewebsites.net/ws/notifications/${userId}/?token=${authToken}`
      );

      socket.onopen = () => {
        reconnectAttempts = 0;
        dispatch(setConnected(true));

        // Fetch milestones on connect if idle
        const storedUserId = localStorage.getItem('user_id');
        if (storedUserId) {
          const uid = parseInt(storedUserId, 10);
          const milestoneState = getState().milestones;
          const status = milestoneState?.status || 'idle';
          if (status === 'idle') {
            dispatch(fetchUserMilestones(uid));
          }
        }

        socket.send(
          JSON.stringify({
            category: 'chat_system',
            action: 'user_online',
          })
        );
      };

      socket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);

          // === Blog Creation Handling ===
          if (data.type === "blog_created") {
            console.log('Blog creation received:', data);
            handleBlogUpload(data, dispatch, getState);
            return;
          }

          // === Blog Share Handling ===
          if (data.type === "blog_shared") {
            console.log('Blog share received:', data);
            handleBlogShared(data, dispatch, getState);
            return;
          }

          // === Blog Unshare Handling ===
          if (data.type === "blog_unshared") {
            console.log('Blog unshare received:', data);
            handleBlogUnshared(data, dispatch, getState);
            return;
          }

          // === Blog Update Handling ===
          if (data.type === 'blog_update') {
            handleBlogUpdateMessage(data, dispatch, getState);
            return;
          }

          // === Blog Modification Handling ===
          if (data.type === 'blog_modified') {
            handleBlogModified(data, dispatch, getState);
            return;
          }

          // === Blog Comment Handling ===
          if (data.type === 'comment_update') {
            handleCommentUpdateMessage(data, dispatch, getState);
            return;
          }

          // === Blog Comment Like Handling ===
          if (data.type === 'comment_like_update') {
            handleCommentLikeUpdateMessage(data, dispatch, getState);
            return;
          }

          // === Reply Update Handling ===
          if (data.type === 'reply_update') {
            handleReplyUpdateMessage(data, dispatch, getState);
            return;
          }

          // === Milestone Notification Handling ===
          if (data?.notification?.notification_type === 'Milestone_Notification') {
            console.log('Milestone Notification received:', data.notification);
            const milestoneNotification = {
              notification_type: 'Milestone_Notification' as const,
              notification_message: data.notification.notification_message,
              notification_data: data.notification.notification_data,
              notification_number: data.notification.notification_number,
              notification_freshness: data.notification.notification_freshness,
              created_at: data.notification.created_at,
            };
            console.log('Dispatching Milestone Notification:', milestoneNotification);

            dispatch(addNotification(milestoneNotification));

            // Send deletion command to server for this milestone notification
            const deletionMessage = JSON.stringify({
              action: 'delete_notification',
              notification_type: 'Milestone_Notification',
              notification_number: data.notification.notification_number,
            });

            if (socket.readyState === WebSocket.OPEN) {
              socket.send(deletionMessage);
              console.log('Sent deletion message for Milestone notification:', deletionMessage);
            }

            return;
          }

          // === Chat System and Other Notification Messages ===
          if (data?.type === 'notification_message' && data?.category === 'chat_system') {
            handleChatSystemMessage(data, dispatch, getState);
          } else if (data?.notification) {
            dispatch(addNotification(data.notification));
          } else if (data?.delete_notification) {
            const { notification_type, notification_number } = data.delete_notification;
            if (notification_type && notification_number) {
              dispatch(
                removeNotificationByDetails({
                  notification_type,
                  notification_number,
                })
              );
            }
          }
        } catch (error) {
          console.error('Message parsing error:', error);
        }
      };

      socket.onclose = (event: CloseEvent) => {
        dispatch(setConnected(false));
        if (![4000, 4001].includes(event.code)) {
          reconnectAttempts++;
          const delay = getReconnectDelay();
          setTimeout(() => {
            const storedUserId = localStorage.getItem('user_id');
            if (storedUserId) dispatch(connectWebSocket(storedUserId) as any);
          }, delay);
        }
      };

      socket.onerror = (error: Event) => {
        console.error('WebSocket error:', error);
        socket.close();
      };

      dispatch(setSocket(socket));
    } catch (error) {
      console.error('Connection failed:', error);
      const delay = getReconnectDelay();
      setTimeout(() => dispatch(connectWebSocket(userId) as any), delay);
    }
  };

// === Disconnect WebSocket Thunk ===
export const disconnectWebSocket =
  () => (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();
    if (notifications.socket) {
      notifications.socket.close(4000, 'User initiated disconnect');
      dispatch(setSocket(null));
      dispatch(setConnected(false));
    }
  };

// === Send Message Over WebSocket Thunk ===
export const sendWebSocketMessage =
  (notificationType: string, messagetype: string, data: Record<string, any>) =>
  (dispatch: AppDispatch, getState: () => RootState) => {
    const { notifications } = getState();
    if (notifications.socket && notifications.socket.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ notificationType, messagetype, ...data });
      notifications.socket.send(message);
    } else {
      console.error('WebSocket is not connected');
      const storedUserId = localStorage.getItem('user_id');
      if (storedUserId) dispatch(connectWebSocket(storedUserId) as any);
    }
  };