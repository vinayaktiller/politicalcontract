import React, { useState, useEffect } from 'react';
import api from '../../../api';
import './ClaimContributionForm.css';
import CircleContactsModal from '../blogrelated/BlogCreator/CircleContacts/CircleContactsModal';
import { fetchCircleContacts, selectCircleContacts, selectCircleStatus } from '../blogrelated/BlogCreator/CircleContacts/circleContactsSlice';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch } from '../../../store';
import UserBox from '../mygroups/GroupDetailsPage/UserBox/UserBox';
import ConflictModal from './ConflictModal/ConflictModal';

interface TeamMember {
  id: number;
  name: string;
  profile_pic: string | null;
  audience_count: number;
  shared_audience_count: number;
}

interface OwnerDetails {
  id: number;
  name: string;
  profile_pic: string | null;
}

interface Contribution {
  id: string;
  link: string;
  title: string;
  owner: number;
  created_at: string;
  owner_details?: OwnerDetails;
}

interface DisputedData {
  title: string;
  description: string;
  teammembers: number[];
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
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showContactsModal, setShowContactsModal] = useState(false);
  const [validatingIds, setValidatingIds] = useState(false);
  
  // Conflict reporting state
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [existingContribution, setExistingContribution] = useState<Contribution | null>(null);
  const [conflictData, setConflictData] = useState({
    conflict_type: 'ownership',
    explanation: '',
    evidence_urls: [] as string[],
    current_evidence_url: ''
  });
  const [disputedData, setDisputedData] = useState<DisputedData>({
    title: '',
    description: '',
    teammembers: []
  });
  const [submittingConflict, setSubmittingConflict] = useState(false);
  const [conflictSubmitted, setConflictSubmitted] = useState(false);

  const dispatch = useDispatch<AppDispatch>();
  const contacts = useSelector(selectCircleContacts);
  const contactsStatus = useSelector(selectCircleStatus);

  useEffect(() => {
    if (showContactsModal && contactsStatus === 'idle') {
      dispatch(fetchCircleContacts(false));
    }
  }, [showContactsModal, contactsStatus, dispatch]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (name in conflictData) {
      setConflictData(prev => ({ ...prev, [name]: value }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
    
    setError(null);
  };

  const handleAddEvidenceUrl = () => {
    if (conflictData.current_evidence_url.trim()) {
      setConflictData(prev => ({
        ...prev,
        evidence_urls: [...prev.evidence_urls, prev.current_evidence_url],
        current_evidence_url: ''
      }));
    }
  };

  const handleRemoveEvidenceUrl = (index: number) => {
    setConflictData(prev => ({
      ...prev,
      evidence_urls: prev.evidence_urls.filter((_, i) => i !== index)
    }));
  };

  const handleEvidenceUrlChange = (value: string) => {
    setConflictData(prev => ({
      ...prev,
      current_evidence_url: value
    }));
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

      const response = await api.post('/api/blog_related/contributions/create/', payload);

      // Handle different success messages based on response status
      if (response.status === 200) {
        setSuccessMessage('Contribution claimed successfully! This URL was already being used in blogs and has now been claimed by you.');
      } else if (response.status === 201) {
        setSuccessMessage('Contribution claimed successfully! A new contribution has been created.');
      }
      
      setSuccess(true);
      setFormData({ link: '', title: '', discription: '' });
      setTeamMembers([]);
    } catch (err: any) {
      console.error('Error claiming contribution:', err.response?.data || err.message);
      
      // Handle conflict case
      if (err.response?.status === 409 && err.response.data?.conflict) {
        setExistingContribution(err.response.data.existing_contribution);
        // Store the disputed data for conflict reporting
        setDisputedData({
          title: formData.title,
          description: formData.discription,
          teammembers: teamMembers.map(member => member.id)
        });
        setShowConflictModal(true);
        return;
      }
      
      let errorMsg = 'Failed to claim contribution';
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.response?.data?.link) {
        errorMsg = err.response.data.link[0];
      }
      
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitConflict = async () => {
    setSubmittingConflict(true);
    
    try {
      const userId = localStorage.getItem("user_id");
      if (!userId) {
        setError("User not logged in.");
        setSubmittingConflict(false);
        return;
      }

      const payload = {
        contribution: existingContribution?.id,
        conflict_type: conflictData.conflict_type,
        explanation: conflictData.explanation,
        evidence_urls: conflictData.evidence_urls,
        // Include disputed data in the payload
        disputed_title: disputedData.title,
        disputed_description: disputedData.description,
        disputed_teammembers: disputedData.teammembers
      };

      await api.post('/api/blog_related/contributions/conflict/', payload);
      
      setConflictSubmitted(true);
      setShowConflictModal(false);
      setSuccessMessage('Conflict report submitted successfully. Our team will review it and get back to you.');
      setSuccess(true);
    } catch (err: any) {
      console.error('Error submitting conflict:', err.response?.data || err.message);
      setError('Failed to submit conflict report. Please try again.');
    } finally {
      setSubmittingConflict(false);
    }
  };

  const handleCloseConflictModal = () => {
    setShowConflictModal(false);
    setConflictData({
      conflict_type: 'ownership',
      explanation: '',
      evidence_urls: [],
      current_evidence_url: ''
    });
  };

  return (
    <div className="contribution-page-container">
      <div className="contribution-page-card">
        <div className="contribution-page-header">
          <div className="contribution-icon">📝</div>
          <h1>Claim Your Contribution</h1>
          <p>Share your published work and get the recognition you deserve</p>
        </div>

        {success && (
          <div className="contribution-success-message">
            <svg className="contribution-success-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M11,16.5L18,9.5L16.59,8.09L11,13.67L7.91,10.59L6.5,12L11,16.5Z" />
            </svg>
            <p>{successMessage}</p>
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
                <svg className="contact-icon" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z" />
                </svg>
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
              <>
                <svg className="claim-icon" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1Z" />
                </svg>
                Claim Contribution
              </>
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

      {/* Conflict Modal */}
      <ConflictModal
        show={showConflictModal}
        existingContribution={existingContribution}
        conflictData={conflictData}
        disputedData={disputedData}
        submittingConflict={submittingConflict}
        onClose={handleCloseConflictModal}
        onSubmit={handleSubmitConflict}
        onChange={handleChange}
        onAddEvidenceUrl={handleAddEvidenceUrl}
        onRemoveEvidenceUrl={handleRemoveEvidenceUrl}
        onEvidenceUrlChange={handleEvidenceUrlChange}
      />
    </div>
  );
};

export default ClaimContributionForm;