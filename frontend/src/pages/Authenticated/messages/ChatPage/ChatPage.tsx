import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  AppDispatch,
  RootState,
} from '../../../../store';
import {
  initializeRoom,
  sendNewMessage,
  markMessagesRead,
  addMessage,
  setCurrentRoom,
  removeMessage,
} from './chatSlice';
import {
  selectCurrentRoom,
  selectConversation,
  selectMessages,
  selectChatStatus,
  selectSendStatus,
  selectChatError,
} from './Chatpagetypes';
import {
  Box,
  Typography,
  Avatar,
  CircularProgress,
  TextField,
  IconButton,
  Paper,
  InputAdornment,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { format } from 'date-fns';

const ChatPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();

  // Refs for scroll and reading state
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastMarkedRef = useRef<number>(0);
  const hasNewMessagesRef = useRef<boolean>(false);

  // Local state for message input
  const [messageInput, setMessageInput] = useState('');

  // Redux selectors for chat data
  const room = useSelector(selectCurrentRoom);
  const conversation = useSelector(selectConversation);
  const messages = useSelector(selectMessages);
  const status = useSelector(selectChatStatus);
  const sendStatus = useSelector(selectSendStatus);
  const error = useSelector(selectChatError);

  // Current user info (adapt to your store structure)
  const currentUser = useSelector((state: RootState) => state.user);

  /**
   * Handle marking messages as read, throttled to max once every 2 seconds
   */
  const handleMarkAsRead = useCallback(() => {
    if (!conversationId || !room) return;

    const now = Date.now();
    if (now - lastMarkedRef.current < 2000) return;

    if (hasNewMessagesRef.current) {
      dispatch(markMessagesRead(conversationId));
      hasNewMessagesRef.current = false;
      lastMarkedRef.current = now;
    }
  }, [conversationId, room, dispatch]);

  /**
   * Initialize room once on mount or when conversationId changes
   */
  useEffect(() => {
    if (!conversationId) return;

    dispatch(setCurrentRoom(conversationId));
    dispatch(initializeRoom(conversationId));

    // Optional cleanup if you want to reset state on unmount
    return () => {
      // dispatch(resetRoomState(conversationId));
    };
  }, [conversationId, dispatch]);

  /**
   * Detect new unread messages and mark as read if necessary
   */
  useEffect(() => {
    if (!room) return;

    const hasNewUnread = messages.some(msg => !msg.is_own && !msg.read);

    if (hasNewUnread) {
      hasNewMessagesRef.current = true;
      handleMarkAsRead();
    }
  }, [messages, handleMarkAsRead, room]);

  /**
   * Mark as read on user interactions (focus/click/tab visibility)
   */
  useEffect(() => {
    const handleUserActivity = () => {
      if (document.visibilityState === 'visible') {
        handleMarkAsRead();
      }
    };

    window.addEventListener('focus', handleUserActivity);
    window.addEventListener('click', handleUserActivity);
    document.addEventListener('visibilitychange', handleUserActivity);

    return () => {
      window.removeEventListener('focus', handleUserActivity);
      window.removeEventListener('click', handleUserActivity);
      document.removeEventListener('visibilitychange', handleUserActivity);
    };
  }, [handleMarkAsRead]);

  /**
   * Scroll to bottom whenever messages change
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Send message handler with optimistic UI update using temp ID
   */
  const handleSendMessage = async () => {
    if (!conversationId || !messageInput.trim()) return;

    const content = messageInput.trim();
    const safeSenderName = currentUser?.name ?? 'Unknown Sender';

    // Create optimistic message with temp ID
    const tempId = `temp-${Date.now()}`;
    const optimisticMessage = {
      id: tempId,
      content,
      timestamp: new Date().toISOString(),
      read: true,
      sender_name: safeSenderName,
      sender_profile: null,
      is_own: true,
    };

    // Add optimistic message to state immediately
    dispatch(addMessage({ conversationId, message: optimisticMessage }));

    // Clear input box
    setMessageInput('');

    try {
      // Await real message send fulfillment
      await dispatch(sendNewMessage({ conversationId, content })).unwrap();
      // No need to remove optimistic message here, sendNewMessage thunk will update it upon success
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic message on failure
      dispatch(removeMessage({ conversationId, messageId: tempId }));
      // Optionally show error to user or retry
    }
  };

  /**
   * Support sending message on Enter without shift (shift+enter adds newline)
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Show loading spinner while loading messages initially
  if (status === 'loading' && !messages.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  // Show error message or fallback if no conversation
  if (error || !conversation) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100vh"
        flexDirection="column"
      >
        <Typography variant="h6" color="error">
          {error || 'Conversation not found'}
        </Typography>
        <Typography
          variant="body1"
          sx={{ mt: 2, cursor: 'pointer', textDecoration: 'underline' }}
          onClick={() => navigate(-1)}
        >
          Go back to conversations
        </Typography>
      </Box>
    );
  }

  // Main chat UI rendering
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <Paper
        sx={{
          display: 'flex',
          alignItems: 'center',
          p: 2,
          borderRadius: 0,
          position: 'sticky',
          top: 0,
          zIndex: 10,
          bgcolor: 'background.paper',
        }}
        elevation={1}
      >
        <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }} aria-label="Back to conversations">
          <ArrowBackIcon />
        </IconButton>

        <Avatar
          src={conversation.other_user.profile_pic || undefined}
          alt={conversation.other_user.name}
          sx={{ width: 40, height: 40, mr: 2 }}
        />

        <Typography variant="h6" noWrap>
          {conversation.other_user.name}
        </Typography>
      </Paper>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          bgcolor: '#f9f9f9',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
            }}
          >
            <Typography variant="body1" color="textSecondary">
              No messages yet. Be the first to start the conversation!
            </Typography>
          </Box>
        ) : (
          messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                justifyContent: message.is_own ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  maxWidth: '80%',
                  flexDirection: message.is_own ? 'row-reverse' : 'row',
                  alignItems: 'flex-end',
                }}
              >
                {!message.is_own && (
                  <Avatar
                    src={message.sender_profile || undefined}
                    alt={message.sender_name}
                    sx={{ width: 32, height: 32, mr: 1, ml: 1 }}
                  />
                )}

                <Box>
                  <Box
                    sx={{
                      bgcolor: message.is_own ? '#d1e7ff' : '#ffffff',
                      borderRadius: 3,
                      p: 1.5,
                      boxShadow: 1,
                      maxWidth: '100%',
                      wordBreak: 'break-word',
                    }}
                  >
                    <Typography variant="body1">{message.content}</Typography>
                  </Box>

                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      textAlign: message.is_own ? 'right' : 'left',
                      mt: 0.5,
                      color: 'text.secondary',
                      px: 1,
                    }}
                  >
                    {format(new Date(message.timestamp), 'hh:mm a')}
                    {!message.is_own && !message.read && (
                      <span style={{ marginLeft: 4, color: '#ff6b6b' }}>•</span>
                    )}
                  </Typography>
                </Box>
              </Box>
            </Box>
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Message Input Area */}
      <Paper
        sx={{
          p: 2,
          borderRadius: 0,
          position: 'sticky',
          bottom: 0,
          bgcolor: 'background.paper',
        }}
        elevation={4}
      >
        <TextField
          fullWidth
          multiline
          minRows={1}
          maxRows={6}
          value={messageInput}
          onChange={(e) => setMessageInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          variant="outlined"
          disabled={sendStatus === 'sending'}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  color="primary"
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim() || sendStatus === 'sending'}
                  sx={{ alignSelf: 'flex-end' }}
                  aria-label="send message"
                >
                  {sendStatus === 'sending' ? <CircularProgress size={24} /> : <SendIcon />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Paper>
    </Box>
  );
};

export default ChatPage;
