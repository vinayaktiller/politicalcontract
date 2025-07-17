// src/features/timeline/components/Profiles.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import { ChevronsRight } from "lucide-react";
import { useDispatch } from "react-redux";
import { ProfileData } from "../timelineTypes";
import { updateScrollPosition } from "../timelineSlice";
import '../TimelinePage.css';

interface ProfileDataWithOrigin extends ProfileData {
  origin?: boolean;
}

interface ProfilesProps {
  parentNumber: number;
  profileData: ProfileDataWithOrigin;
  getScrollPosition: () => number;
  timelineNumber: number;
}


const Profiles: React.FC<ProfilesProps> = ({
  parentNumber,
  profileData,
  getScrollPosition,
  timelineNumber
}) => {
  const [currentPropertyIndex, setCurrentPropertyIndex] = useState(0);
  const [isOrigin, setIsOrigin] = useState(false);
  const [imageError, setImageError] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const properties = [
    { label: "Children", value: profileData.childcount },
    { label: "Influence", value: profileData.influence },
    { label: "Height", value: profileData.height },
    { label: "Weight", value: profileData.weight },
  ];

  function getRelation(parentNumber: number): string {
    if (parentNumber === 1) return "parent";
    if (parentNumber === 2) return "Grandparent";
    if (parentNumber >= 3) return `Ancestor ${parentNumber}`;
    return "Unknown";
  }

  useEffect(() => {
    setIsOrigin(!!profileData.origin);
    setImageError(false); // Reset error when profile changes
  }, [profileData]);

  console.log("parentNumber", parentNumber,);
  const handleRightArrowClick = () => {
    if (!profileData.id) return;
    
    const scrollPosition = getScrollPosition();
    dispatch(updateScrollPosition({ 
      timelineNumber, 
      position: scrollPosition 
    }));
    
    navigate(`/children/${profileData.id}`, { 
      state: { 
        profileData, 
        parentNumber,
        timelineNumber,
        timeshift: true 
      } 
    });
  };

  const handleLeftArrow = () => {
    setCurrentPropertyIndex(prev => 
      (prev - 1 + properties.length) % properties.length
    );
  };

  const handleRightArrow = () => {
    setCurrentPropertyIndex(prev => 
      (prev + 1) % properties.length
    );
  };

  return (
    <div className="dynamic-boxes-row">
      <div className="dynamic-boxes-box">
        <div className={isOrigin ? 'profile-head-origin' : 'profile-head'}>
          <h2>{isOrigin ? 'ORIGIN' : getRelation(parentNumber)}</h2>
        </div>

        <div className="profile-body">
          {profileData.profilepic && !imageError ? (
            <img 
              src={profileData.profilepic} 
              alt="Profile" 
              className="box-profile-image" 
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="box-image-placeholder" > {profileData.name.charAt(0)}</div>
          )}
          
          <div className="profile-detail">
            <strong>{profileData.name || "Unknown"}</strong>
          </div>
          
          <div className="profile-detail">
            <strong>ID: {profileData.id || "N/A"}</strong>
          </div>
          
          <div className="profile-navigation">
            <span onClick={handleLeftArrow}>&lt;</span>
            {properties[currentPropertyIndex].label}: {properties[currentPropertyIndex].value}
            <span onClick={handleRightArrow}>&gt;</span>
          </div>
        </div>
      </div>
      
      <ChevronsRight 
        className="dynamic-boxes-arrow-right" 
        onClick={handleRightArrowClick} 
      />
    </div>
  );
};

export default Profiles;