// src/features/chat/ChatPage/ChatPage.tsx
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  AppDispatch,
  RootState,
} from '../../../../store';
import {
  initializeRoom,
  markMessagesRead,
  addOptimisticMessage,
  updateMessage,
  removeMessage,
  setCurrentRoom,
} from './chatSlice';
import {
  selectCurrentRoom,
  selectConversation,
  selectMessages,
  selectChatStatus,
  selectSendStatus,
  selectChatError,
  Message,
} from './Chatpagetypes'; // assuming types exported from this file
import { updateConversation, conversationRead } from '../chatlist/chatListSlice';
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Paper,
  InputAdornment,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ReplayIcon from '@mui/icons-material/Replay';
import { format } from 'date-fns';
import './ChatPage.css';

const StatusIcon = ({ status, isOwn }: { status: string; isOwn: boolean }) => {
  if (!isOwn) return null;

  let className = 'status-icon ';
  const normalizedStatus = status.toLowerCase();

  switch (normalizedStatus) {
    case 'delivered':
    case 'delivered_update':
      className += 'delivered';
      return <span className={className}>✓✓</span>;
    case 'read':
    case 'read_update':
      className += 'read';
      return <span className={className}>✓✓</span>;
    default:
      className += 'sent';
      return <span className={className}>✓</span>;
  }
};

const ChatPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const dispatch: AppDispatch = useDispatch();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastMarkedRef = useRef<number>(0);
  const hasNewMessagesRef = useRef<boolean>(false);
  const [messageInput, setMessageInput] = useState('');

  const room = useSelector(selectCurrentRoom);
  const conversation = useSelector(selectConversation);
  const messages = useSelector(selectMessages);
  const status = useSelector(selectChatStatus);
  const sendStatus = useSelector(selectSendStatus);
  const error = useSelector(selectChatError);
  const currentUser = useSelector((state: RootState) => state.user);
  const socket = useSelector((state: RootState) => state.notifications.socket);

  // MARK AS READ handler - debounced and updates chat list unread count
  const handleMarkAsRead = useCallback(() => {
    if (!conversationId || !room) return;
    const now = Date.now();
    if (now - lastMarkedRef.current < 2000) return; // rate-limit for performance
    if (hasNewMessagesRef.current) {
      // Reset unread count in chat list
      dispatch(
        updateConversation({
          id: conversationId,
          changes: { unread_count: 0 },
          moveToTop: true,
        })
      );

      // Mark messages as read on server
      dispatch(markMessagesRead(conversationId));

      hasNewMessagesRef.current = false;
      lastMarkedRef.current = now;
    }
  }, [conversationId, room, dispatch]);

  // When conversation changes, immediately reset unread count in chat list
  useEffect(() => {
    if (conversationId) {
      dispatch(
        updateConversation({
          id: conversationId,
          changes: { unread_count: 0 },
          moveToTop: true,
        })
      );
    }
  }, [conversationId, dispatch]);

  // Init room and data
  useEffect(() => {
    if (!conversationId) return;
    dispatch(setCurrentRoom(conversationId));
    dispatch(initializeRoom(conversationId));
    dispatch(conversationRead(conversationId));
  }, [conversationId, dispatch]);

  // Mark as read when new messages come in
  useEffect(() => {
    if (!room) return;
    const hasNewUnread = messages.some(
      (msg) =>
        !msg.is_own &&
        ['sent', 'delivered', 'delivered_update', 'Sent', 'Delivered', 'Delivered Update'].includes(
          msg.status
        )
    );
    if (hasNewUnread) {
      hasNewMessagesRef.current = true;
      handleMarkAsRead();
    }
  }, [messages, handleMarkAsRead, room]);

  // Listen to focus/visibility changes and mark as read
  useEffect(() => {
    const handleUserActivity = () => {
      if (document.visibilityState === 'visible') handleMarkAsRead();
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

  // Autoscroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Resend functionality for failed/sending messages
  const handleResendMessage = (message: Message) => {
    if (!conversationId) return;

    dispatch(removeMessage({ conversationId, messageId: message.id }));

    const newTempId = `temp-${Date.now()}`;
    const optimisticMessage = {
      ...message,
      id: newTempId,
      timestamp: new Date().toISOString(),
      status: 'sent',
    };

    dispatch(addOptimisticMessage({ conversationId, message: optimisticMessage }));

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          category: 'chat_system',
          action: 'send_message',
          conversation_id: conversationId,
          content: message.content,
          temp_id: newTempId,
        })
      );
    }
  };

  // Send message with optimistic update & chat list update
  const handleSendMessage = async () => {
    if (!conversationId || !messageInput.trim()) return;

    const content = messageInput.trim();
    const safeSenderName = currentUser?.name ?? 'You';
    const tempId = `temp-${Date.now()}`;

    const optimisticMessage: Message = {
      id: tempId,
      content,
      timestamp: new Date().toISOString(),
      status: 'sent',
      sender_name: safeSenderName,
      sender_profile: currentUser?.profile_pic ?? null,
      is_own: true,
    };

    dispatch(addOptimisticMessage({ conversationId, message: optimisticMessage }));
    setMessageInput('');

    // Update chat list with new message details immediately
    dispatch(
      updateConversation({
        id: conversationId,
        changes: {
          last_message: content,
          last_message_timestamp: optimisticMessage.timestamp,
        },
        moveToTop: true,
      })
    );

    try {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(
          JSON.stringify({
            category: 'chat_system',
            action: 'send_message',
            conversation_id: conversationId,
            content,
            temp_id: tempId,
          })
        );
      } else {
        throw new Error('WebSocket not connected');
      }
    } catch (error) {
      dispatch(removeMessage({ conversationId, messageId: tempId }));
      console.error('Failed to send message:', error);
    }
  };

  // Send message on Enter key (without shift)
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Render loading state
  if (status === 'loading' && messages.length === 0) {
    return (
      <Box className="chat-page-loading">
        <div className="loading-spinner"></div>
      </Box>
    );
  }

  // Render error or missing conversation state
  if (error || !conversation) {
    return (
      <Box className="chat-page-error">
        <Typography variant="h6" className="error-message">
          {error || 'Conversation not found'}
        </Typography>
        <Typography variant="body1" className="back-link" onClick={() => navigate(-1)}>
          Go back to conversations
        </Typography>
      </Box>
    );
  }

  return (
    <Box className="chat-page-container">
      <Paper className="chat-header">
        <IconButton onClick={() => navigate(-1)} className="back-button" aria-label="Go back">
          <ArrowBackIcon />
        </IconButton>

        {conversation.other_user.profile_pic ? (
          <img
            src={conversation.other_user.profile_pic}
            alt={conversation.other_user.name}
            className="profile-pic"
          />
        ) : (
          <div className="profile-pic-placeholder">{conversation.other_user.name.charAt(0)}</div>
        )}
        <Typography className="user-name">{conversation.other_user.name}</Typography>
      </Paper>

      <Box className="messages-container">
        {messages.length === 0 ? (
          <Box className="no-messages">
            <Typography variant="body1">No messages yet. Be the first to start the conversation!</Typography>
          </Box>
        ) : (
          <>
            {messages.map((message) => (
              <Box
                key={message.id}
                className={`message-bubble ${message.is_own ? 'own-message' : 'other-message'}`}
              >
                {!message.is_own &&
                  (message.sender_profile ? (
                    <img
                      src={message.sender_profile}
                      alt={message.sender_name}
                      className="message-profile-pic"
                    />
                  ) : (
                    <div className="message-profile-pic placeholder">{message.sender_name.charAt(0)}</div>
                  ))}

                <Box className="message-content">
                  <Typography className="message-text">{message.content}</Typography>
                  <Box className="message-time">
                    <span>{format(new Date(message.timestamp), 'hh:mm a')}</span>
                    <StatusIcon status={message.status} isOwn={message.is_own} />

                    {message.is_own && message.status === 'sent' && (
                      <IconButton
                        size="small"
                        onClick={() => handleResendMessage(message)}
                        className="retry-button"
                        aria-label="Retry sending message"
                      >
                        {/* <ReplayIcon fontSize="small" /> */}
                      </IconButton>
                    )}
                  </Box>
                </Box>
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </Box>

      <Paper className="message-input-container">
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
                  aria-label="send message"
                  className="send-button"
                >
                  {sendStatus === 'sending' ? <span className="sending-spinner" /> : <SendIcon />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          className="message-input"
        />
      </Paper>
    </Box>
  );
};

export default ChatPage;
