import React from 'react';
import '../styles.css';

interface ProfileImageProps {
  imageUrl: string;
  name: string;
}

const ProfileImage: React.FC<ProfileImageProps> = ({ imageUrl, name }) => {
  return (
    <img
      loading="lazy"
      src={imageUrl || '/default-profile.png'}
      alt={`Profile of ${name}`}
      className="conn-profile-image"
      onError={(e) => {
        (e.target as HTMLImageElement).src = '/default-profile.png';
      }}
    />
  );
};

export default ProfileImage;