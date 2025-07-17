// ProfileImage.tsx
import React from 'react';

interface ProfileImageProps {
    imageUrl: string;
    name: string;
}

const ProfileImage: React.FC<ProfileImageProps> = ({ imageUrl, name }) => {
    return (
        <div className="GroupSpeakerInvitation-profile-container">
            <img 
                src={imageUrl} 
                alt={`${name}'s profile`} 
                className="GroupSpeakerInvitation-profile-image"
                onError={(e) => e.currentTarget.src = "default-profile.png"}
            />
           
        </div>
    );
};

export default ProfileImage;