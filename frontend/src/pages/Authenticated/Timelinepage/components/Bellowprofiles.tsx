import React, { useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import { ChevronsRight, ChevronsDown } from "lucide-react";
import { useDispatch } from "react-redux";
import { ProfileData } from "../timelineTypes";
import { updateScrollPosition } from "../timelineSlice";
import '../TimelinePage.css';

interface BellowprofilesProps {
  parentNumber: number;
  last: number;
  profileData: ProfileData;
  getScrollPosition: () => number;
  timelineNumber: number;
  onShiftPath: (id: number) => void;
  isEndPoint: boolean; // Added endpoint prop
}

const Bellowprofiles: React.FC<BellowprofilesProps> = ({
  parentNumber,
  last,
  profileData,
  getScrollPosition,
  timelineNumber,
  onShiftPath,
  isEndPoint // Using passed endpoint status
}) => {
  const [currentPropertyIndex, setCurrentPropertyIndex] = useState(0);
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
    if (parentNumber === 0) return "You";
    if (parentNumber === 1) return "Children";
    if (parentNumber === 2) return "Grandchild";
    if (parentNumber >= 3) return `Descendant ${parentNumber}`;
    return "Unknown";
  }

  useEffect(() => {
    setImageError(false);
  }, [profileData]);

  const handleRightArrowClick = () => {
    if (!profileData.id) return;
    
    const scrollPosition = getScrollPosition();
    dispatch(updateScrollPosition({ timelineNumber, position: scrollPosition }));
    
    navigate(`/children/${profileData.id}`, { 
      state: { 
        profileData, 
        parentNumber,
        timelineNumber,
        endPoint: isEndPoint, // Passing endpoint status
      } 
    });
  };

  const handleDownArrowClick = () => {
    if (!profileData.id) return;
    
    onShiftPath(profileData.id);
    
    const scrollPosition = getScrollPosition();
    dispatch(updateScrollPosition({ timelineNumber, position: scrollPosition }));
    
    navigate(`/children/${profileData.id}`, { 
      state: { 
        profileData, 
        endPoint: isEndPoint, // Passing endpoint status
        timelineNumber 
      } 
    });
  };

  const handlePropertyNavigation = (direction: 'prev' | 'next') => {
    setCurrentPropertyIndex(prev => 
      direction === 'prev' 
        ? (prev - 1 + properties.length) % properties.length
        : (prev + 1) % properties.length
    );
  };

  return (
    <div className='cent'>
      <div className="dynamic-boxes-row">
        <div className={`dynamic-boxes-box ${isEndPoint ? "highlight-box-endpoint" : ""}`}>
          <div className='profile-head'>
            <h3>{getRelation(parentNumber)}</h3>
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
              <div className="box-image-placeholder">
                {profileData.name?.charAt(0) || "?"}
              </div>
            )}
            
            <div className="profile-detail">
              <strong>{profileData.name || "Unknown"}</strong>
            </div>
            
            <div className="profile-detail">
              <strong>ID: {profileData.id || "N/A"}</strong>
            </div>
            
            <div className="profile-navigation">
              <span onClick={() => handlePropertyNavigation('prev')}>&lt;</span>
              {properties[currentPropertyIndex].label}: {properties[currentPropertyIndex].value}
              <span onClick={() => handlePropertyNavigation('next')}>&gt;</span>
            </div>
          </div>
        </div>
        
        {!isEndPoint && (
          <ChevronsRight
            className="dynamic-boxes-arrow-right"
            onClick={handleRightArrowClick}
          />
        )}
      </div>
      
      {isEndPoint && profileData.childcount > 0 && (
        <ChevronsDown 
          className="dynamic-boxes-down-right" 
          onClick={handleDownArrowClick} 
        />
      )}
    </div>
  );
};

export default Bellowprofiles;