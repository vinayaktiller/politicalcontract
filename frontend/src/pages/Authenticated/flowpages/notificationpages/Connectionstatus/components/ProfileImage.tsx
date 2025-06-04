import React from 'react';


interface ProfileImageProps {
    imageUrl: string;
    name: string;
}

const ProfileImage: React.FC<ProfileImageProps> = ({ imageUrl, name }) => {
    return (
        <div className="profile-image-container">
            <img 
                src={imageUrl} 
                alt={`${name}'s profile`} 
                className="profile-image"
                onError={(e) => e.currentTarget.src = "default-profile.png"} // Fallback image
            />
            <p className="profile-name">{name}</p>
        </div>
    );
};

export default ProfileImage;
