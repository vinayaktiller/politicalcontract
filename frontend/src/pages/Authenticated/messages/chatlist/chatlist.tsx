// src/features/chat/ChatList/ChatList.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../../../../store';
import {
  fetchConversations,
  conversationRead,
  addNewConversation,   // <--- import this action
} from './chatListSlice';
import { fetchContacts } from './contacts/contactsSlice';
import './ChatList.css';
import ContactsModal from './contacts/ContactsModal';
import { setCurrentRoom } from '../ChatPage/chatSlice';
import api from '../../../../api';

interface UserProfile {
  id: number;
  name: string;
  profile_pic?: string | null;
}

interface Conversation {
  id: string;
  last_message: string | null;
  last_message_timestamp: string | null;
  unread_count: number;
  other_user: UserProfile;
}

const ChatList: React.FC = () => {
  const dispatch: AppDispatch = useDispatch();
  const navigate = useNavigate();

  const { entities, ids } = useSelector((state: RootState) => state.chatList);
  const conversations = ids.map(id => entities[id]).filter(Boolean) as Conversation[];

  const contacts = useSelector((state: RootState) => state.contacts.contacts);
  const contactsStatus = useSelector((state: RootState) => state.contacts.status);

  const status = useSelector((state: RootState) => state.chatList.status);
  const error = useSelector((state: RootState) => state.chatList.error);

  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
  const [showContactsModal, setShowContactsModal] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [startingContact, setStartingContact] = useState<number | null>(null);
  const [isStartingConversation, setIsStartingConversation] = useState(false);

  useEffect(() => {
    dispatch(setCurrentRoom('0'));
    dispatch(fetchConversations(false));
    dispatch(fetchContacts(false));
  }, [dispatch]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        dispatch(fetchConversations(true)),
        dispatch(fetchContacts(true)),
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatTime = (timestamp: string | null): string => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getLastMessagePreview = (message: string | null): string => {
    if (!message) return 'No messages yet';
    return message.length > 40 ? message.substring(0, 37) + '...' : message;
  };

  const handleImageError = (id: string) => {
    setImageErrors(prev => ({ ...prev, [id]: true }));
  };

  const handleConversationClick = (conversationId: string) => {
    dispatch(conversationRead(conversationId));
    navigate(`/chat/${conversationId}`);
  };

  const handleNewConversation = async (contactId: number) => {
    if (isStartingConversation) return;
    setStartingContact(contactId);
    setIsStartingConversation(true);

    interface StartConversationResponse {
      conversation_id: string;
    }

    try {
      const response = await api.post<StartConversationResponse>(`/api/chat/conversation/start/${contactId}/`);
      const { conversation_id } = response.data;

      // Dispatch addNewConversation with the newly started conversation info
      dispatch(addNewConversation({
        id: conversation_id,
        last_message: null,
        last_message_timestamp: null,
        unread_count: 0,
        other_user: contacts.find(c => c.id === contactId)!,
      }));

      setShowContactsModal(false);
      setStartingContact(null);
      setIsStartingConversation(false);

      dispatch(conversationRead(conversation_id));
      navigate(`/chat/${conversation_id}`);

      // Optionally still refresh chat list to sync state fully
      dispatch(fetchConversations(true));
    } catch (error) {
      console.error('Failed to start conversation', error);
      alert('Failed to start conversation. Please try again.');
      setStartingContact(null);
      setIsStartingConversation(false);
    }
  };

  const handleExistingConversation = (conversationId: string) => {
    if (isStartingConversation) return;
    dispatch(conversationRead(conversationId));
    navigate(`/chat/${conversationId}`);
    setShowContactsModal(false);
  };

  if (status === 'loading' && !isRefreshing) {
    return <div className="chat-list-loading">Loading conversations...</div>;
  }

  if (error) {
    return <div className="user-error">Error: {error}</div>;
  }

  return (
    <div className="chat-list-container">
      <div className="chat-list-header">
        <h2>Messages</h2>
        <div className="header-buttons">
          <button
            className="contacts-button"
            onClick={() => setShowContactsModal(true)}
            aria-label="Open Contacts Modal"
          >
            Contacts
          </button>
        </div>
      </div>

      <div className="conversations-list">
        {conversations.length === 0 ? (
          <div className="no-conversations">No conversations yet</div>
        ) : (
          conversations.map(conv => (
            <div
              key={conv.id}
              className="conversation-item"
              onClick={() => handleConversationClick(conv.id)}
              role="button"
              tabIndex={0}
              onKeyDown={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleConversationClick(conv.id);
                }
              }}
              aria-label={`Conversation with ${conv.other_user.name}`}
            >
              <div className="user-info">
                {conv.other_user.profile_pic && !imageErrors[conv.id] ? (
                  <img
                    src={conv.other_user.profile_pic}
                    alt={conv.other_user.name}
                    className="profile-pic"
                    onError={() => handleImageError(conv.id)}
                    loading="lazy"
                  />
                ) : (
                  <div className="profile-pic-placeholder">{conv.other_user.name.charAt(0)}</div>
                )}
                <div className="user-details">
                  <div className="user-name">{conv.other_user.name}</div>
                  <div className="last-message">
                    {getLastMessagePreview(conv.last_message)}
                  </div>
                </div>
              </div>

              <div className="message-meta">
                <div className="timestamp">{formatTime(conv.last_message_timestamp)}</div>
                {conv.unread_count > 0 && (
                  <div className="unread-count" aria-label={`${conv.unread_count} unread messages`}>
                    {conv.unread_count}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {showContactsModal && (
        <ContactsModal
          contacts={contacts}
          loading={contactsStatus === 'loading'}
          onClose={() => setShowContactsModal(false)}
          onNewConversation={handleNewConversation}
          onExistingConversation={handleExistingConversation}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          isStartingConversation={isStartingConversation}
          startingContactId={startingContact}
        />
      )}
    </div>
  );
};

export default ChatList;
