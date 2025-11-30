import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../../store"
import { fetchNetworkActivity, refreshNetworkActivity } from './heartbeatNetworkSlice';
import HeartbeatGraph from '../HeartbeatGraph/HeartbeatGraph';
import './HeartbeatNetworkPage.css';

interface NetworkUser {
  id: number;
  name: string;
  profile_pic: string | null;
  connection_type: string;
  is_active_today: boolean;
  streak_count: number;
  activity_history: Array<{ date: string; active: boolean }>;
}

interface ActivityUpdate {
  user_id: number;
  is_active_today: boolean;
  streak_count: number;
}

const HeartbeatNetworkPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [selectedUser, setSelectedUser] = useState<NetworkUser | null>(null);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  const [isInitialLoad, setIsInitialLoad] = useState<boolean>(true);
  
  const { 
    networkUsers, 
    currentUserId, 
    today, 
    status, 
    error 
  } = useSelector((state: RootState) => state.heartbeatNetwork);

  // Remove duplicates from networkUsers (additional safety)
  const uniqueNetworkUsers = React.useMemo(() => {
    const seen = new Set();
    return networkUsers.filter(user => {
      if (seen.has(user.id)) {
        return false;
      }
      seen.add(user.id);
      return true;
    });
  }, [networkUsers]);

  // Get current state for backend check
  const getCurrentState = () => {
    const activeUsers = uniqueNetworkUsers.filter(user => user.is_active_today);
    const inactiveUsers = uniqueNetworkUsers.filter(user => !user.is_active_today);
    
    return {
      activeIds: activeUsers.map(user => user.id).join(','),
      inactiveIds: inactiveUsers.map(user => user.id).join(',')
    };
  };

  // Fetch data every time component mounts
  useEffect(() => {
    if (isInitialLoad) {
      // First load - fetch all data without parameters
      dispatch(fetchNetworkActivity());
      setIsInitialLoad(false);
    } else {
      // Subsequent loads - send current state to check for updates
      const { activeIds, inactiveIds } = getCurrentState();
      dispatch(refreshNetworkActivity({ activeIds, inactiveIds }));
    }
  }, [dispatch, isInitialLoad]);

  // Auto-select user when data loads
  useEffect(() => {
    if (uniqueNetworkUsers.length > 0 && !selectedUser) {
      const activeUsers = uniqueNetworkUsers.filter(user => user.is_active_today);
      if (activeUsers.length > 0) {
        setSelectedUser(activeUsers[0]);
      } else {
        setSelectedUser(uniqueNetworkUsers[0]);
      }
    }
  }, [uniqueNetworkUsers, selectedUser]);

  const handleUserClick = (user: NetworkUser) => {
    setSelectedUser(user);
  };

  const handleImageError = (userId: number) => {
    setImageErrors(prev => new Set(prev).add(userId));
  };

  const handleManualRefresh = () => {
    const { activeIds, inactiveIds } = getCurrentState();
    dispatch(refreshNetworkActivity({ activeIds, inactiveIds }));
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive ? '#2ecc71' : '#e74c3c';
  };

  const getStatusText = (isActive: boolean) => {
    return isActive ? 'Active' : 'Inactive';
  };

  const getConnectionTypeDisplay = (type: string) => {
    const typeMap: { [key: string]: string } = {
      'initiate': 'Initiate',
      'initiator': 'Initiator',
      'group_member': 'Group Member',
      'connection': 'Connection',
      'online_initiate': 'Online Initiate',
      'online_initiator': 'Online Initiator',
      'agent': 'Agent',
      'members': 'Member',
      'speaker': 'Speaker',
      'audience': 'Audience',
      'groupagent': 'Group Agent',
      'groupmembers': 'Group Member',
      'multiplespeakers': 'Multiple Speakers',
      'shared_audience': 'Shared Audience'
    };
    return typeMap[type] || type;
  };

  // Get first letter of first name for placeholder
  const getFirstLetter = (name: string) => {
    return name.split(' ')[0]?.charAt(0) || '?';
  };

  // Filter active and inactive users from unique list
  const activeUsers = uniqueNetworkUsers.filter(user => user.is_active_today);
  const inactiveUsers = uniqueNetworkUsers.filter(user => !user.is_active_today);

  if (status === 'loading') {
    return (
      <div className="heartbeat-network-page">
        <div className="heartbeat-network-loading">
          <div className="heartbeat-spinner"></div>
          <p>Loading network activity...</p>
        </div>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="heartbeat-network-page">
        <div className="heartbeat-network-error">
          <h3>Error Loading Network</h3>
          <p>{error}</p>
          <button 
            onClick={() => {
              if (isInitialLoad) {
                dispatch(fetchNetworkActivity());
              } else {
                const { activeIds, inactiveIds } = getCurrentState();
                dispatch(refreshNetworkActivity({ activeIds, inactiveIds }));
              }
            }}
            className="retry-button"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="heartbeat-network-page">
      <div className="heartbeat-network-header">
        <h1>Network Heartbeat</h1>
        <p>View activity status of your connections ({uniqueNetworkUsers.length} total)</p>
        
        <div className="network-stats">
          <div className="stat-item">
            <span className="stat-number" style={{color: '#2ecc71'}}>
              {activeUsers.length}
            </span>
            <span className="stat-label">Active Today</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">{uniqueNetworkUsers.length}</span>
            <span className="stat-label">Total Connections</span>
          </div>
          <div className="stat-item">
            <button 
              onClick={handleManualRefresh}
              className="retry-button"
              style={{marginTop: '10px'}}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="heartbeat-network-content">
        <div className="network-users-list">
          <div className="users-section">
            <h3>Active Today ({activeUsers.length})</h3>
            <div className="users-grid">
              {activeUsers.map(user => (
                <NetworkUserCard
                  key={user.id}
                  user={user}
                  isSelected={selectedUser?.id === user.id}
                  onClick={handleUserClick}
                  onImageError={handleImageError}
                  imageErrors={imageErrors}
                  getFirstLetter={getFirstLetter}
                  getStatusColor={getStatusColor}
                  getStatusText={getStatusText}
                  getConnectionTypeDisplay={getConnectionTypeDisplay}
                />
              ))}
            </div>
          </div>

          {inactiveUsers.length > 0 && (
            <div className="users-section">
              <h3>Inactive Today ({inactiveUsers.length})</h3>
              <div className="users-grid">
                {inactiveUsers.map(user => (
                  <NetworkUserCard
                    key={user.id}
                    user={user}
                    isSelected={selectedUser?.id === user.id}
                    onClick={handleUserClick}
                    onImageError={handleImageError}
                    imageErrors={imageErrors}
                    getFirstLetter={getFirstLetter}
                    getStatusColor={getStatusColor}
                    getStatusText={getStatusText}
                    getConnectionTypeDisplay={getConnectionTypeDisplay}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="user-detail-view">
          {selectedUser ? (
            <div className="selected-user-details">
              <div className="detail-header">
                <div className="author-header">
                  {selectedUser.profile_pic && !imageErrors.has(selectedUser.id) ? (
                    <img 
                      src={selectedUser.profile_pic} 
                      alt={selectedUser.name}
                      className="author-photo-large"
                      onError={() => handleImageError(selectedUser.id)}
                    />
                  ) : (
                    <div className="author-photo-placeholder-large">
                      {getFirstLetter(selectedUser.name)}
                    </div>
                  )}
                </div>
                <div className="detail-info">
                  <h2 className="author-name">{selectedUser.name}</h2>
                  <p className="detail-connection-type">
                    {getConnectionTypeDisplay(selectedUser.connection_type)}
                  </p>
                  <div className="detail-stats">
                    <div 
                      className="detail-status"
                      style={{ color: getStatusColor(selectedUser.is_active_today) }}
                    >
                      {getStatusText(selectedUser.is_active_today)} Today
                    </div>
                    <div className="detail-streak">
                      Current Streak: <strong>{selectedUser.streak_count} days</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div className="user-activity-graph">
                <h3>Activity History (Last 30 Days)</h3>
                <HeartbeatGraph activityHistory={selectedUser.activity_history} />
              </div>
            </div>
          ) : (
            <div className="no-user-selected">
              <div className="selection-prompt">
                <div className="prompt-icon">👆</div>
                <h3>Select a connection</h3>
                <p>Click on any user from the list to view their detailed activity history and heartbeat status</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Network User Card Component
interface NetworkUserCardProps {
  user: NetworkUser;
  isSelected: boolean;
  onClick: (user: NetworkUser) => void;
  onImageError: (userId: number) => void;
  imageErrors: Set<number>;
  getFirstLetter: (name: string) => string;
  getStatusColor: (isActive: boolean) => string;
  getStatusText: (isActive: boolean) => string;
  getConnectionTypeDisplay: (type: string) => string;
}

const NetworkUserCard: React.FC<NetworkUserCardProps> = ({ 
  user, 
  isSelected, 
  onClick, 
  onImageError,
  imageErrors,
  getFirstLetter,
  getStatusColor,
  getStatusText,
  getConnectionTypeDisplay
}) => {

  return (
    <div
      className={`network-user-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onClick(user)}
    >
      <div className="user-avatar">
        {user.profile_pic && !imageErrors.has(user.id) ? (
          <img 
            src={user.profile_pic} 
            alt={user.name}
            className="author-photo"
            onError={() => onImageError(user.id)}
          />
        ) : (
          <div className="author-photo-placeholder">
            {getFirstLetter(user.name)}
          </div>
        )}
      </div>
      
      <div className="user-info">
        <h4 className="user-name">{user.name}</h4>
        <p className="connection-type">
          {getConnectionTypeDisplay(user.connection_type)}
        </p>
        <div className="user-stats">
          <span 
            className="status-badge"
            style={{ 
              backgroundColor: getStatusColor(user.is_active_today),
              color: 'white'
            }}
          >
            {getStatusText(user.is_active_today)}
          </span>
          <span className="streak-count">🔥 {user.streak_count} days</span>
        </div>
      </div>
    </div>
  );
};

export default HeartbeatNetworkPage;