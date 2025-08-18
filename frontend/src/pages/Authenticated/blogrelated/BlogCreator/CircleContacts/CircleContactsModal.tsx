import React from 'react';

interface CircleContact {
  id: number;
  name: string;
  profile_pic: string | null;
  relation: string;
}

interface CircleContactsModalProps {
  contacts: CircleContact[];
  loading: boolean;
  onClose: () => void;
  onSelect: (contactId: number) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const CircleContactsModal: React.FC<CircleContactsModalProps> = ({
  contacts,
  loading,
  onClose,
  onSelect,
  onRefresh,
  isRefreshing,
}) => {

  console.log('CircleContactsModal Props:', { contacts, loading, isRefreshing });
  return (
    <div className="modal-backdrop">
      <div className="contacts-modal">
        <div className="modal-header">
          <button className="close-button" onClick={onClose} aria-label="Close Contacts Modal">×</button>
          <h2>Your Circle Contacts</h2>
          <button
            className="modal-refresh-button"
            onClick={onRefresh}
            disabled={isRefreshing}
            aria-label="Refresh Contacts"
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
                onClick={() => onSelect(contact.id)}
                role="button"
                tabIndex={0}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect(contact.id);
                  }
                }}
                aria-label={`Contact ${contact.name}`}
              >
                <div className="contact-info">
                  {contact.profile_pic ? (
                    <img
                      src={contact.profile_pic}
                      alt={contact.name}
                      className="contact-profile-pic"
                      loading="lazy"
                    />
                  ) : (
                    <div className="contact-profile-placeholder">{contact.name.charAt(0)}</div>
                  )}
                  <div className="contact-details">
                    <span className="contact-name">{contact.name}</span>
                    {/* <span className="contact-relation">{contact.relation}</span> */}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CircleContactsModal;