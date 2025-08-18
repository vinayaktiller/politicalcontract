
// src/components/BlogCreator/ProfileHeader.tsx
import React from 'react';

interface ProfileHeaderProps {
  name: string;
  profilePic: string;
  onUserJourney?: boolean;
  targetName?: string;
}

const ProfileHeader: React.FC<ProfileHeaderProps> = ({ 
  name, 
  profilePic, 
  onUserJourney = true,
  targetName
}) => {
  return (
    <div className="profile-header">
      <div className="profile-pic-container">
        <img 
          src={profilePic || '/default-profile.png'} 
          alt={name} 
          className="profile-pic" 
          onError={(e) => {
            e.currentTarget.src = '/default-profile.png';
          }}
        />
      </div>
      <div className="profile-info">
        {onUserJourney ? (
          <div className="journey-indicator">
            <span className="journey-label">on your journey</span>
          </div>
        ) : (
          <div className="journey-indicator">
            <span className="journey-label">On the journey of</span>
            <span className="target-name">{targetName}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileHeader;