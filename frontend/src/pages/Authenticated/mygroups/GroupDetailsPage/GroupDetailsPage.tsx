import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../../api';
import UserBox from './UserBox/UserBox';
import './GroupDetailsPage.css';

interface User {
  id: number;
  name: string;
  profilepic: string | null;
  audience_count: number;
  shared_audience_count: number;
}

interface GroupDetails {
  group_id: number;
  group_name: string;
  profile_pic: string | null;
  founder: User;
  speakers: User[];
  members: User[];
  outside_agents: User[];
  institution: string;
  links: string[];
  photos: string[];
  date_created: string;
  country: string;
  state: string;
  district: string;
  subdistrict: string;
  village: string;
}

const GroupDetailsPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const [group, setGroup] = useState<GroupDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGroup = async () => {
      try {
        const response = await api.get<GroupDetails>(`/api/event/group/${groupId}/details/`);
        setGroup(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to load group details');
      } finally {
        setLoading(false);
      }
    };

    fetchGroup();
  }, [groupId]);

  if (loading) {
    return (
      <div className="gdp-loading">
        <div className="gdp-loading-spinner"></div>
        <p>Loading group details...</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="gdp-error">
        <div className="gdp-error-icon">⚠️</div>
        <p>{error || 'Group not found'}</p>
        <button 
          className="gdp-back-button"
          onClick={() => navigate('/my-groups')}
        >
          Back to Groups
        </button>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Build location string from available parts
  const locationParts = [
    group.village,
    group.subdistrict,
    group.district,
    group.state,
    group.country
  ].filter(part => part).join(', ');

  return (
    <div className="gdp-container">
      {/* Group Header */}
      <div className="gdp-header">
        {group.profile_pic ? (
          <img 
            src={group.profile_pic} 
            alt={group.group_name} 
            className="gdp-photo"
          />
        ) : (
          <div className="gdp-photo-placeholder">
            {group.group_name.charAt(0)}
          </div>
        )}
        <h1 className="gdp-name">{group.group_name}</h1>
        <div className="gdp-meta">
          {locationParts && (
            <div className="gdp-meta-item">
              <span className="gdp-meta-label">Location:</span>
              <span className="gdp-meta-value">{locationParts}</span>
            </div>
          )}
          {group.institution && (
            <div className="gdp-meta-item">
              <span className="gdp-meta-label">Institution:</span>
              <span className="gdp-meta-value">{group.institution}</span>
            </div>
          )}
          <div className="gdp-meta-item">
            <span className="gdp-meta-label">Created:</span>
            <span className="gdp-meta-value">{formatDate(group.date_created)}</span>
          </div>
        </div>
      </div>

      {/* Links Section - only if links exist */}
      {group.links && group.links.length > 0 && (
        <div className="gdp-section gdp-links-section">
          <h2 className="gdp-section-title">Links</h2>
          <div className="gdp-links-container">
            {group.links.map((link, index) => (
              <a 
                key={index} 
                href={link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="gdp-link"
              >
                {link}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Founder Section */}
      <div className="gdp-section gdp-founder-section">
        <h2 className="gdp-section-title">Founder</h2>
        <div className="gdp-user-box-container">
          <UserBox 
            user={group.founder} 
            relation="Founder" 
            isOrigin={true} 
          />
        </div>
      </div>

      {/* Speakers Section - only if speakers exist */}
      {group.speakers.length > 0 && (
        <div className="gdp-section gdp-speakers-section">
          <h2 className="gdp-section-title">Speakers</h2>
          <div className="gdp-user-boxes-container">
            {group.speakers.map(speaker => (
              <UserBox 
                key={speaker.id} 
                user={speaker} 
                relation="Speaker" 
              />
            ))}
          </div>
        </div>
      )}

      {/* Members Section - only if members exist */}
      {group.members.length > 0 && (
        <div className="gdp-section gdp-members-section">
          <h2 className="gdp-section-title">Members</h2>
          <div className="gdp-user-boxes-container">
            {group.members.map(member => (
              <UserBox 
                key={member.id} 
                user={member} 
                relation="Member" 
              />
            ))}
          </div>
        </div>
      )}

      {/* Outside Agents Section - only if agents exist */}
      {group.outside_agents.length > 0 && (
        <div className="gdp-section gdp-agents-section">
          <h2 className="gdp-section-title">Outside Agents</h2>
          <div className="gdp-user-boxes-container">
            {group.outside_agents.map(agent => (
              <UserBox 
                key={agent.id} 
                user={agent} 
                relation="Agent" 
              />
            ))}
          </div>
        </div>
      )}

      {/* Photos Section - only if photos exist */}
      {group.photos && group.photos.length > 0 && (
        <div className="gdp-section gdp-photos-section">
          <h2 className="gdp-section-title">Photos</h2>
          <div className="gdp-photos-container">
            {group.photos.map((photo, index) => (
              <div key={index} className="gdp-photo-item">
                <img 
                  src={photo} 
                  alt={`Group photo ${index + 1}`} 
                  className="gdp-photo"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      <button 
        className="gdp-back-button"
        onClick={() => navigate('/my-groups')}
      >
        Back to Groups
      </button>
    </div>
  );
};

export default GroupDetailsPage;