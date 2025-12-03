import React from 'react';
import UserBox from '../../mygroups/GroupDetailsPage/UserBox/UserBox';
import './ConflictModal.css';

interface OwnerDetails {
  id: number;
  name: string;
  profile_pic: string | null;
}

interface Contribution {
  id: string;
  link: string;
  title: string;
  type: string;
  owner: number;
  created_at: string;
  owner_details?: OwnerDetails;
}

interface DisputedData {
  title: string;
  description: string;
  type: string;
  teammembers: number[];
}

interface ConflictModalProps {
  show: boolean;
  existingContribution: Contribution | null;
  conflictData: {
    conflict_type: string;
    explanation: string;
    evidence_urls: string[];
    current_evidence_url: string;
  };
  disputedData: DisputedData;
  submittingConflict: boolean;
  onClose: () => void;
  onSubmit: () => void;
  onChange: (e: React.ChangeEvent<HTMLSelectElement | HTMLTextAreaElement>) => void;
  onAddEvidenceUrl: () => void;
  onRemoveEvidenceUrl: (index: number) => void;
  onEvidenceUrlChange: (value: string) => void;
}

const contributionTypeLabels: { [key: string]: string } = {
  'article': '📝 Article',
  'video': '🎬 Video',
  'podcast': '🎙️ Podcast',
  'code': '💻 Code/Repository',
  'design': '🎨 Design/Artwork',
  'research': '🔬 Research Paper',
  'other': '📦 Other',
  'none': 'Not Specified'
};

const ConflictModal: React.FC<ConflictModalProps> = ({
  show,
  existingContribution,
  conflictData,
  disputedData,
  submittingConflict,
  onClose,
  onSubmit,
  onChange,
  onAddEvidenceUrl,
  onRemoveEvidenceUrl,
  onEvidenceUrlChange
}) => {
  if (!show) return null;

  return (
    <div className="modal-overlay">
      <div className="conflict-modal">
        <div className="conflict-modal-header">
          <h2>Contribution Already Claimed</h2>
          <button 
            className="close-modal-btn"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        
        <div className="conflict-modal-content">
          <p>
            This URL has already been claimed by another user. If you believe this is an error,
            please report the issue below.
          </p>
          
          {existingContribution && (
            <div className="existing-contribution-info">
              <h4>Existing Claim Details:</h4>
              <p><strong>URL:</strong> {existingContribution.link}</p>
              <p><strong>Title:</strong> {existingContribution.title || 'No title provided'}</p>
              <p><strong>Type:</strong> {contributionTypeLabels[existingContribution.type] || 'Not specified'}</p>
              <p><strong>Claimed by:</strong></p>
              
              {existingContribution.owner_details && (
                <div className="owner-details">
                  <UserBox 
                    user={{
                      id: existingContribution.owner_details.id,
                      name: existingContribution.owner_details.name,
                      profilepic: existingContribution.owner_details.profile_pic,
                      audience_count: 0,
                      shared_audience_count: 0
                    }} 
                    relation="Owner" 
                    isOrigin={false} 
                  />
                </div>
              )}
              
              <p><strong>Claimed on:</strong> {new Date(existingContribution.created_at).toLocaleDateString()}</p>
              
              {/* Show disputed data */}
              <div className="disputed-data-section">
                <h4>Your Claim Details:</h4>
                <p><strong>Your Title:</strong> {disputedData.title || 'No title provided'}</p>
                <p><strong>Your Type:</strong> {contributionTypeLabels[disputedData.type] || 'Not specified'}</p>
                <p><strong>Your Description:</strong> {disputedData.description || 'No description provided'}</p>
                {disputedData.teammembers.length > 0 && (
                  <div>
                    <p><strong>Your Team Members:</strong></p>
                    <div className="team-members-list">
                      {disputedData.teammembers.map(id => (
                        <span key={id} className="team-member-id">User #{id}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <div className="conflict-form">
            <div className="conflict-form-group">
              <label>Conflict Type</label>
              <select
                name="conflict_type"
                value={conflictData.conflict_type}
                onChange={onChange}
              >
                <option value="ownership">Ownership Dispute - I am the true owner</option>
                <option value="collaboration">Collaboration - I worked on this but someone else claimed it</option>
                <option value="unauthorized">Unauthorized Use - Someone claimed my work without permission</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div className="conflict-form-group">
              <label>Explanation</label>
              <textarea
                name="explanation"
                value={conflictData.explanation}
                onChange={onChange}
                placeholder="Please explain why you believe you should be the owner of this contribution..."
                rows={4}
              />
            </div>
            
            <div className="conflict-form-group">
              <label>Evidence URLs (optional)</label>
              <div className="evidence-url-input">
                <input
                  type="url"
                  value={conflictData.current_evidence_url}
                  onChange={(e) => onEvidenceUrlChange(e.target.value)}
                  placeholder="https://example.com/evidence"
                />
                <button 
                  type="button" 
                  onClick={onAddEvidenceUrl}
                  disabled={!conflictData.current_evidence_url.trim()}
                >
                  Add
                </button>
              </div>
              
              {conflictData.evidence_urls.length > 0 && (
                <div className="evidence-urls-list">
                  {conflictData.evidence_urls.map((url, index) => (
                    <div key={index} className="evidence-url-item">
                      <span>{url}</span>
                      <button 
                        type="button" 
                        onClick={() => onRemoveEvidenceUrl(index)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="conflict-modal-actions">
          <button
            type="button"
            className="cancel-btn"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="submit-conflict-btn"
            onClick={onSubmit}
            disabled={submittingConflict || !conflictData.explanation.trim()}
          >
            {submittingConflict ? 'Submitting...' : 'Submit Conflict Report'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConflictModal;