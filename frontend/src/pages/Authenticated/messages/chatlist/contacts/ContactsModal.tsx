import React from 'react';
import '../../chatlist/ChatList.css';

interface Contact {
    id: number;
    name: string;
    profile_pic?: string;
    has_conversation: boolean;
    conversation_id: string | null;
}

interface ContactsModalProps {
    contacts: Contact[];
    loading: boolean;
    onClose: () => void;
    onNewConversation: (contactId: number) => void;
    onExistingConversation: (conversationId: string) => void;
    onRefresh: () => void;
    isRefreshing: boolean;
}

const ContactsModal: React.FC<ContactsModalProps> = ({ 
    contacts, 
    loading, 
    onClose, 
    onNewConversation,
    onExistingConversation,
    onRefresh,
    isRefreshing
}) => {
    return (
        <div className="modal-backdrop">
            <div className="contacts-modal">
                <div className="modal-header">
                    <button className="close-button" onClick={onClose}>×</button>
                    <h2>Contacts</h2>
                    <button 
                        className="modal-refresh-button"
                        onClick={onRefresh}
                        disabled={isRefreshing}
                    >
                        {isRefreshing ? 'Refreshing...' : 'Refresh'}
                    </button>
                </div>
                
                {loading ? (
                    <div className="modal-loading">Loading contacts...</div>
                ) : !contacts || contacts.length === 0 ? (
                    <div className="modal-no-contacts">No contacts available</div>
                ) : (
                    <div className="contacts-list">
                        {contacts.map(contact => (
                            <div 
                                key={contact.id} 
                                className="contact-item"
                                onClick={() => {
                                    if (contact.has_conversation && contact.conversation_id) {
                                        onExistingConversation(contact.conversation_id);
                                    } else {
                                        onNewConversation(contact.id);
                                    }
                                }}
                            >
                                <div className="contact-info">
                                    {contact.profile_pic ? (
                                        <img
                                            src={contact.profile_pic}
                                            alt={contact.name}
                                            className="contact-profile-pic"
                                        />
                                    ) : (
                                        <div className="contact-profile-placeholder">
                                            {contact.name.charAt(0)}
                                        </div>
                                    )}
                                    <span className="contact-name">{contact.name}</span>
                                </div>
                                <div className="contact-status">
                                    {contact.has_conversation ? (
                                        <span className="chat-exists">Chat exists</span>
                                    ) : (
                                        <span className="start-chat">Start chat</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ContactsModal;