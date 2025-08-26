// ClaimContributionForm.tsx
import React, { useState, useEffect } from 'react';
import api from '../../../api';
import './ClaimContributionForm.css';
import CircleContactsModal from '../blogrelated/BlogCreator/CircleContacts/CircleContactsModal';
import { fetchCircleContacts, selectCircleContacts, selectCircleStatus } from '../blogrelated/BlogCreator/CircleContacts/circleContactsSlice';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch } from '../../../store';
import UserBox from '../mygroups/GroupDetailsPage/UserBox/UserBox';

interface TeamMember {
  id: number;
  name: string;
  profile_pic: string | null;
  audience_count: number;
  shared_audience_count: number;
}

const ClaimContributionForm = () => {
  const [formData, setFormData] = useState({
    link: '',
    title: '',
    discription: ''
  });
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [manualIdInput, setManualIdInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showContactsModal, setShowContactsModal] = useState(false);
  const [validatingIds, setValidatingIds] = useState(false);

  const dispatch = useDispatch<AppDispatch>();
  const contacts = useSelector(selectCircleContacts);
  const contactsStatus = useSelector(selectCircleStatus);

  useEffect(() => {
    if (showContactsModal && contactsStatus === 'idle') {
      dispatch(fetchCircleContacts(false));
    }
  }, [showContactsModal, contactsStatus, dispatch]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError(null);
  };

  const handleAddFromContacts = (contactId: number) => {
    const contact = contacts.find(c => c.id === contactId);
    if (contact && !teamMembers.some(m => m.id === contactId)) {
      setTeamMembers(prev => [...prev, {
        id: contact.id,
        name: contact.name,
        profile_pic: contact.profile_pic,
        audience_count: 0,
        shared_audience_count: 0
      }]);
    }
    setShowContactsModal(false);
  };

  const handleAddManualId = async () => {
    if (!manualIdInput.trim()) return;
    
    const ids = manualIdInput.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
    if (ids.length === 0) return;
    
    setValidatingIds(true);
    try {
      const response = await api.post('/api/blog_related/validate-users/', {
        user_ids: ids
      });
      
      const data = response.data as { valid_users: TeamMember[] };
      const newMembers = data.valid_users.filter(
        (user: TeamMember) => !teamMembers.some(m => m.id === user.id)
      );
      
      setTeamMembers(prev => [...prev, ...newMembers]);
      setManualIdInput('');
    } catch (err) {
      setError('Failed to validate user IDs');
    } finally {
      setValidatingIds(false);
    }
  };

  const removeTeamMember = (id: number) => {
    setTeamMembers(prev => prev.filter(member => member.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSuccess(false);
    setError(null);

    try {
      const userId = localStorage.getItem("user_id");
      if (!userId) {
        setError("User not logged in. Please log in to claim your contribution.");
        setIsSubmitting(false);
        return;
      }

      const teamMemberIds = teamMembers.map(member => member.id);
      
      const payload = {
        ...formData,
        owner: parseInt(userId, 10),
        teammembers: teamMemberIds
      };

      console.log("Submitting contribution payload:", payload);

      await api.post('/api/blog_related/contributions/create/', payload);

      setSuccess(true);
      setFormData({ link: '', title: '', discription: '' });
      setTeamMembers([]);
    } catch (err: any) {
      console.error('Error claiming contribution:', err.response?.data || err.message);
      const errorMsg =
        err.response?.data?.detail ||
        err.response?.data?.link?.[0] || 
        'Failed to claim contribution';
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="contribution-page-container">
      <div className="contribution-page-card">
        <div className="contribution-page-header">
          <h1>Claim Your Contribution</h1>
          <p>Share your published work and get recognition</p>
        </div>

        {success && (
          <div className="contribution-success-message">
            <svg className="contribution-success-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,16.5L18,9.5L16.59,8.09L11,13.67L7.91,10.59L6.5,12L11,16.5Z" />
            </svg>
            <p>Contribution claimed successfully!</p>
          </div>
        )}

        {error && (
          <div className="contribution-error-message">
            <svg className="contribution-error-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
            </svg>
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="contribution-page-form">
          <div className="form-fields-container">
            <div className="contribution-form-group">
              <label htmlFor="link">Content URL *</label>
              <input
                type="url"
                id="link"
                name="link"
                value={formData.link}
                onChange={handleChange}
                placeholder="https://example.com/your-content"
                required
                className={error?.includes('URL') ? 'contribution-input-error' : ''}
              />
              <div className="contribution-input-hint">
                Paste the direct link to your published content
              </div>
            </div>

            <div className="contribution-form-group">
              <label htmlFor="title">Title</label>
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="My Amazing Article/Video"
              />
              <div className="contribution-input-hint">
                A descriptive title for your contribution
              </div>
            </div>

            <div className="contribution-form-group">
              <label htmlFor="discription">Description</label>
              <textarea
                id="discription"
                name="discription"
                value={formData.discription}
                onChange={handleChange}
                placeholder="Briefly describe your contribution..."
                rows={4}
              />
              <div className="contribution-input-hint">
                Optional details about your work
              </div>
            </div>
          </div>

          {/* Team Members Section */}
          <div className="contribution-form-group team-members-section">
            <label>Team Members</label>
            <div className="team-members-input-container">
              <button 
                type="button" 
                className="add-from-contacts-btn"
                onClick={() => setShowContactsModal(true)}
              >
                Add from Contacts
              </button>
              <span className="or-separator">or</span>
              <div className="manual-id-input">
                <input
                  type="text"
                  value={manualIdInput}
                  onChange={(e) => setManualIdInput(e.target.value)}
                  placeholder="Enter user IDs (comma separated)"
                  disabled={validatingIds}
                />
                <button 
                  type="button" 
                  onClick={handleAddManualId}
                  disabled={validatingIds || !manualIdInput.trim()}
                >
                  {validatingIds ? 'Validating...' : 'Add IDs'}
                </button>
              </div>
            </div>
            
            {/* Selected Team Members */}
            {teamMembers.length > 0 && (
              <div className="selected-team-members">
                <h4>Selected Team Members:</h4>
                <div className="team-members-grid">
                  {teamMembers.map(member => (
                    <div key={member.id} className="team-member-box-wrapper">
                      <UserBox 
                        user={{
                          id: member.id,
                          name: member.name,
                          profilepic: member.profile_pic,
                          audience_count: member.audience_count,
                          shared_audience_count: member.shared_audience_count
                        }} 
                        relation="Team Member" 
                        isOrigin={false} 
                      />
                      <button 
                        type="button" 
                        onClick={() => removeTeamMember(member.id)}
                        className="remove-member-btn"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            className="contribution-submit-btn"
            disabled={isSubmitting || !formData.link}
          >
            {isSubmitting ? (
              <>
                <span className="contribution-spinner"></span> Processing...
              </>
            ) : (
              'Claim Contribution'
            )}
          </button>

          <div className="contribution-form-footer">
            <p>By claiming, you verify this is your original content</p>
          </div>
        </form>
      </div>

      {/* Contacts Modal */}
      {showContactsModal && (
        <CircleContactsModal
          contacts={contacts}
          loading={contactsStatus === 'loading'}
          onClose={() => setShowContactsModal(false)}
          onSelect={handleAddFromContacts}
          onRefresh={() => dispatch(fetchCircleContacts(true))}
          isRefreshing={contactsStatus === 'loading'}
        />
      )}
    </div>
  );
};

export default ClaimContributionForm;