// MyGroupsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../../api';
import './styles.css'; // Import your CSS styles

interface Group {
  group_id: number;
  group_name: string;
  group_type: 'unstarted' | 'old';
  date_created: string;
  profile_pic: string | null;
}

const MyGroupsPage: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true);
        const response = await api.get<{ groups: Group[] }>('/api/event/user-groups/', {
          // params: { user_id: 11021801300001 } // Replace with actual user ID
        });
        setGroups(response.data.groups);
        setError(null);
      } catch (err: any) {
        console.error('Fetch Error:', err);
        setError(err.response?.data?.error || 'Failed to fetch groups');
      } finally {
        setLoading(false);
      }
    };

    fetchGroups();
  }, []);

  const handleGroupClick = (group: Group) => {
    if (group.group_type === 'unstarted') {
      navigate(`/group/setup/${group.group_id}`);
    } else {
      navigate(`/group/${group.group_id}`);
    }
  };

  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  if (loading) {
    return (
      <div className="groups-loading">
        <div className="loading-spinner"></div>
        <p>Loading your groups...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="groups-error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button 
          className="retry-button"
          onClick={() => window.location.reload()}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="groups-empty">
        <div className="empty-icon">📁</div>
        <h2>No Groups Found</h2>
        <p>You haven't joined any groups yet</p>
        <button 
          className="create-button"
          onClick={() => navigate('/create-group')}
        >
          Create Your First Group
        </button>
      </div>
    );
  }

  return (
    <div className="groups-container">
      <h1 className="groups-header">My Groups</h1>
      
      <div className="groups-grid">
        {groups.map(group => (
          <div 
            key={group.group_id} 
            className={`group-card ${group.group_type}`}
            onClick={() => handleGroupClick(group)}
          >
            {group.profile_pic ? (
              <img 
                src={group.profile_pic} 
                alt={group.group_name} 
                className="group-image"
              />
            ) : (
              <div className="group-image-placeholder">
                {group.group_name.charAt(0)}
              </div>
            )}
            
            <div className="group-info">
              <h3 className="group-name">{group.group_name}</h3>
              <p className="group-date">
                Created: {formatDate(group.date_created)}
              </p>
              
              <div className="group-type-badge">
                {group.group_type === 'unstarted' ? 'Setup Needed' : 'Active Group'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyGroupsPage;