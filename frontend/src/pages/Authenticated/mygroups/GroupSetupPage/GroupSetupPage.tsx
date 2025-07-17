import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../../api';
import './GroupSetupPage.css';

interface User {
  id: number;
  name: string;
  profilepic: string | null;
}

interface GroupDetails {
  group_id: number;
  group_name: string;
  founder: User;
  speakers: User[];
  pending_speakers_details: User[];
  members: number[]; // Added members field
}

const GroupSetupPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const [group, setGroup] = useState<GroupDetails | null>(null);
  const [speakerId, setSpeakerId] = useState<string>('');
  const [validatedUser, setValidatedUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState<boolean>(false);

  useEffect(() => {
    const fetchGroup = async () => {
      try {
        const response = await api.get<GroupDetails>(`/api/event/group/${groupId}/`);
        setGroup(response.data);
        
        // Redirect if group has members (setup already completed)
        if (response.data.members && response.data.members.length > 0) {
          navigate(`/group/${response.data.group_id}`);
          return;
        }
        
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to load group details');
      } finally {
        setLoading(false);
      }
    };

    fetchGroup();
  }, [groupId, navigate]);

  const validateSpeaker = async () => {
    if (!speakerId.trim()) {
      setError('Please enter a user ID');
      return;
    }

    try {
      setLoading(true);
      const response = await api.post(`/api/event/group/${groupId}/verify-speaker/`, {
        user_id: speakerId
      });
      setValidatedUser((response.data as { user: User }).user);
      setError(null);
    } catch (err: any) {
      setValidatedUser(null);
      setError(err.response?.data?.error || 'Invalid user ID or not eligible');
    } finally {
      setLoading(false);
    }
  };

  const addPendingSpeaker = async () => {
    if (!validatedUser || !group) return;

    try {
      setIsAdding(true);
      await api.post(`/api/event/group/${groupId}/add-pending-speaker/`, {
        user_id: validatedUser.id
      });
      
      // Refetch group data to get updated list
      const response = await api.get<GroupDetails>(`/api/event/group/${groupId}/`);
      setGroup(response.data);
      
      setSuccess(`Added ${validatedUser.name} as pending speaker!`);
      setValidatedUser(null);
      setSpeakerId('');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to add speaker');
    } finally {
      setIsAdding(false);
    }
  };

  const completeSetup = () => {
    navigate(`/group/${groupId}`);
  };

  if (loading) {
    return (
      <div className="setup-loading">
        <div className="loading-spinner"></div>
        <p>Loading group details...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="setup-error">
        <div className="error-icon">⚠️</div>
        <p>{error || 'Group not found'}</p>
        <button 
          className="back-button"
          onClick={() => navigate('/my-groups')}
        >
          Back to Groups
        </button>
      </div>
    );
  }

  return (
    <div className="group-setup-container">
      <h1 className="setup-header">Setup Group: {group.group_name}</h1>
      
      <div className="setup-section">
        <h2>Add Speakers</h2>
        <p className="section-description">
          Enter user IDs to add speakers to your group. Speakers will need to 
          accept your invitation before they can participate.
        </p>
        
        <div className="speaker-input-section">
          <div className="input-group">
            <input
              type="text"
              value={speakerId}
              onChange={(e) => setSpeakerId(e.target.value)}
              placeholder="Enter user ID"
              disabled={isAdding}
            />
            <button 
              onClick={validateSpeaker}
              disabled={isAdding}
              className="validate-button"
            >
              Validate
            </button>
          </div>
          
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}
          
          {validatedUser && (
            <div className="validated-user">
              <div className="user-info">
                {validatedUser.profilepic ? (
                  <img 
                    src={validatedUser.profilepic} 
                    alt={validatedUser.name}
                    className="user-avatar"
                  />
                ) : (
                  <div className="avatar-placeholder">
                    {validatedUser.name.charAt(0)}
                  </div>
                )}
                <div>
                  <h3>{validatedUser.name}</h3>
                  <p>ID: {validatedUser.id}</p>
                </div>
              </div>
              <button 
                onClick={addPendingSpeaker}
                disabled={isAdding}
                className="add-button"
              >
                {isAdding ? 'Adding...' : 'Add as Speaker'}
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Confirmed Speakers Section */}
      <div className="setup-section">
        <h2>Confirmed Speakers</h2>
        {group.speakers.length === 0 ? (
          <p className="no-speakers">No confirmed speakers yet</p>
        ) : (
          <ul className="speaker-list">
            {group.speakers.map(user => (
              <li key={user.id} className="speaker-item">
                <div className="user-info">
                  {user.profilepic ? (
                    <img 
                      src={user.profilepic} 
                      alt={user.name}
                      className="user-avatar"
                    />
                  ) : (
                    <div className="avatar-placeholder">
                      {user.name.charAt(0)}
                    </div>
                  )}
                  <span>{user.name}</span>
                </div>
                <span className="confirmed-status">Confirmed</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      
      {/* Pending Speakers Section */}
      <div className="setup-section">
        <h2>Pending Speakers</h2>
        {group.pending_speakers_details.length === 0 ? (
          <p className="no-pending">No pending speakers yet</p>
        ) : (
          <ul className="pending-list">
            {group.pending_speakers_details.map(user => (
              <li key={user.id} className="pending-item">
                <div className="user-info">
                  {user.profilepic ? (
                    <img 
                      src={user.profilepic} 
                      alt={user.name}
                      className="user-avatar"
                    />
                  ) : (
                    <div className="avatar-placeholder">
                      {user.name.charAt(0)}
                    </div>
                  )}
                  <span>{user.name}</span>
                </div>
                <span className="pending-status">Awaiting</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <div className="setup-actions">
        <button 
          onClick={() => navigate('/my-groups')}
          className="secondary-button"
        >
          Back to Groups
        </button>
        <button 
          onClick={completeSetup}
          className="primary-button"
          disabled={isAdding}
        >
          Complete Setup
        </button>
      </div>
    </div>
  );
};

export default GroupSetupPage;