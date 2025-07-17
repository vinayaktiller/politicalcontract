import React, { useState } from 'react';
import './UserBox.css';

interface User {
  id: number;
  name: string;
  profilepic: string | null;
  audience_count: number;
  shared_audience_count: number;
}

interface UserBoxProps {
  user: User;
  relation: string;
  isOrigin?: boolean;
}

const UserBox: React.FC<UserBoxProps> = ({ user, relation, isOrigin = false }) => {
  const [currentPropertyIndex, setCurrentPropertyIndex] = useState(0);
  
  const properties = [
    { label: "Audience", value: user.audience_count },
    { label: "Shared Audience", value: user.shared_audience_count },
  ];

  const handleLeftArrow = () => {
    setCurrentPropertyIndex((prevIndex) => 
      (prevIndex - 1 + properties.length) % properties.length
    );
  };

  const handleRightArrow = () => {
    setCurrentPropertyIndex((prevIndex) => 
      (prevIndex + 1) % properties.length
    );
  };

  return (
    <div className="gub-box">
      <div className={isOrigin ? 'gub-header gub-origin' : 'gub-header'}>
        <h3>{relation}</h3>
      </div>
      <div className="gub-body">
        {user.profilepic ? (
          <img 
            src={user.profilepic} 
            alt={user.name} 
            className="gub-avatar"
          />
        ) : (
          <div className="gub-avatar-placeholder">
            {user.name.charAt(0)}
          </div>
        )}
        <div className="gub-info">
          <div className="gub-name">{user.name}</div>
          <div className="gub-id">ID: {user.id}</div>
        </div>
        <div className="gub-stats-navigation">
          <span className="gub-nav-arrow" onClick={handleLeftArrow}>&lt;</span>
          <div className="gub-stat">
            {properties[currentPropertyIndex].label}: {properties[currentPropertyIndex].value}
          </div>
          <span className="gub-nav-arrow" onClick={handleRightArrow}>&gt;</span>
        </div>
      </div>
    </div>
  );
};

export default UserBox;