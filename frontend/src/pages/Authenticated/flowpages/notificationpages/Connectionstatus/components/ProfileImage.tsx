// ProfileImage.tsx
import React from 'react';

interface ProfileImageProps {
    imageUrl: string;
    name: string;
}

const ProfileImage: React.FC<ProfileImageProps> = ({ imageUrl, name }) => {
    return (
        <div className="cs-profile-container">
            <img 
                src={imageUrl} 
                alt={`${name}'s profile`} 
                className="cs-profile-image"
                onError={(e) => e.currentTarget.src = "default-profile.png"}
            />
            <p className="cs-profile-name">{name}</p>
        </div>
    );
};

export default ProfileImage;