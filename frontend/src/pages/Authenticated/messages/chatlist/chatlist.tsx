import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../../../../store';
import { 
    fetchConversations, 
    conversationRead
} from './chatListSlice';
import { fetchContacts } from './contacts/contactsSlice';
import './ChatList.css';
import ContactsModal from './contacts/ContactsModal';

interface UserProfile {
    id: number;
    name: string;
    profile_pic?: string;
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
    const conversations = ids.map((id) => entities[id]);
    const contacts = useSelector((state: RootState) => state.contacts.contacts);
    const contactsStatus = useSelector((state: RootState) => state.contacts.status);
    
    const status = useSelector((state: RootState) => state.chatList.status);
    const error = useSelector((state: RootState) => state.chatList.error);
    const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
    const [showContactsModal, setShowContactsModal] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);

    useEffect(() => {
        dispatch(fetchConversations(false));
        dispatch(fetchContacts(false));
    }, [dispatch]);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            await Promise.all([
                dispatch(fetchConversations(true)),
                dispatch(fetchContacts(true))
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

    const handleNewConversation = (contactId: number) => {
        // Start new conversation logic
        console.log('Starting new conversation with contact:', contactId);
        setShowContactsModal(false);
    };

    const handleExistingConversation = (conversationId: string) => {
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
                    >
                        Contacts
                    </button>
                </div>
            </div>

            <div className="conversations-list">
                {conversations.length === 0 ? (
                    <div className="no-conversations">No conversations yet</div>
                ) : (
                    conversations.map((conv) => (
                        <div 
                            key={conv.id} 
                            className="conversation-item"
                            onClick={() => handleConversationClick(conv.id)}
                        >
                            <div className="user-info">
                                {conv.other_user.profile_pic && !imageErrors[conv.id] ? (
                                    <img
                                        src={conv.other_user.profile_pic}
                                        alt={conv.other_user.name}
                                        className="profile-pic"
                                        onError={() => handleImageError(conv.id)}
                                    />
                                ) : (
                                    <div className="profile-pic-placeholder">
                                        {conv.other_user.name.charAt(0)}
                                    </div>
                                )}
                                <div className="user-details">
                                    <div className="user-name">{conv.other_user.name}</div>
                                    <div className="last-message">
                                        {getLastMessagePreview(conv.last_message)}
                                    </div>
                                </div>
                            </div>

                            <div className="message-meta">
                                <div className="timestamp">
                                    {formatTime(conv.last_message_timestamp)}
                                </div>
                                {conv.unread_count > 0 && (
                                    <div className="unread-count">{conv.unread_count}</div>
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
                />
            )}
        </div>
    );
};

export default ChatList;