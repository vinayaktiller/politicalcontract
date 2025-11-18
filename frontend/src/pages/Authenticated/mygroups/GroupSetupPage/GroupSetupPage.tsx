import React, { useState, useEffect, useRef } from 'react';
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
  profile_pic: string | null;
  founder: User;
  speakers: User[];
  pending_speakers_details: User[];
  members: number[];
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
  const [uploadingProfilePic, setUploadingProfilePic] = useState<boolean>(false);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  console.log("group", group);

  useEffect(() => {
    // Get current user ID from localStorage
    const userId = localStorage.getItem('user_id');
    if (userId) {
      setCurrentUserId(parseInt(userId));
    }

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

  // Check if current user is the group founder
  const isGroupFounder = currentUserId && group && currentUserId === group.founder.id;

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

  const handleProfilePicUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !group) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setError('Please select a valid image file (JPEG, PNG, GIF, WebP)');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size too large. Maximum size is 5MB');
      return;
    }

    // Validate image dimensions for landscape
    const img = new Image();
    img.onload = async () => {
      const isLandscape = img.width > img.height;
      if (!isLandscape) {
        setError('Please upload a landscape-oriented photo (width greater than height)');
        return;
      }

      try {
        setUploadingProfilePic(true);
        setError(null);

        const formData = new FormData();
        formData.append('profile_pic', file);

        const response = await api.patch(
          `/api/event/group/${groupId}/upload-profile-picture/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        setGroup((response.data as { group: GroupDetails }).group);
        setSuccess('Group profile picture uploaded successfully!');
        setTimeout(() => setSuccess(null), 3000);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to upload profile picture');
      } finally {
        setUploadingProfilePic(false);
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    };

    img.onerror = () => {
      setError('Failed to load image. Please try another file.');
    };

    img.src = URL.createObjectURL(file);
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
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
      
      {/* Profile Picture Upload Section - Only show for founder */}
      {isGroupFounder && (
        <div className="setup-section">
          <h2>Group Profile Picture</h2>
          <p className="section-description">
            Upload a landscape-oriented profile picture for your group. This will be visible to all group members.
            <br />
            <strong>Recommended:</strong> Landscape photo with group of people (width greater than height)
          </p>
          
          <div className="profile-pic-section">
            <div className="current-profile-pic">
              {group.profile_pic ? (
                <img 
                  src={group.profile_pic} 
                  alt="Group profile"
                  className="group-profile-pic"
                />
              ) : (
                <div className="group-profile-pic-placeholder">
                  <div className="placeholder-icon">🏞️</div>
                  <span>No group photo yet</span>
                </div>
              )}
            </div>
            
            <div className="upload-controls">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleProfilePicUpload}
                accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                style={{ display: 'none' }}
              />
              <button 
                onClick={triggerFileInput}
                disabled={uploadingProfilePic}
                className="upload-button"
              >
                {uploadingProfilePic ? 'Uploading...' : 'Upload Group Photo'}
              </button>
              <p className="upload-hint">
                Supported formats: JPEG, PNG, GIF, WebP. Max size: 5MB
                <br />
                <strong>Must be landscape orientation</strong>
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Show current profile picture to non-founders */}
      {!isGroupFounder && group.profile_pic && (
        <div className="setup-section">
          <h2>Group Profile Picture</h2>
          <div className="profile-pic-section">
            <div className="current-profile-pic">
              <img 
                src={group.profile_pic} 
                alt="Group profile"
                className="group-profile-pic"
              />
            </div>
            <div className="view-only-message">
              <p>Group profile picture (view only)</p>
              <span>Only the group founder can update this photo</span>
            </div>
          </div>
        </div>
      )}
      
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
          disabled={isAdding || uploadingProfilePic}
        >
          Complete Setup
        </button>
      </div>
    </div>
  );
};

export default GroupSetupPage;