import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import type { AppDispatch } from "../../../../store";
import { ChildProfile } from "../../Timelinepage/timelineTypes";
import { addTimeline, fetchTimelineTail, shiftTimelinePathThunk } from "../../Timelinepage/timelineSlice";
import '../css/ChildrenPage.css';

interface SmallProfileProps {
  profile: ChildProfile;
  timelineNumber: number;
  parentNumber?: number;
  timeshift?: boolean;
  endPoint: boolean;
  isTimelineContext: boolean; // Added to determine context
}

const SmallProfile: React.FC<SmallProfileProps> = ({
  profile,
  timelineNumber,
  parentNumber,
  timeshift = false,
  endPoint,
  isTimelineContext
}) => {
  const [currentPropertyIndex, setCurrentPropertyIndex] = useState(0);
  const [imageError, setImageError] = useState(false);
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const properties = [
    { label: "Children", value: profile.childcount },
    { label: "Influence", value: profile.influence },
    { label: "Depth", value: profile.depth },
    { label: "Weight", value: profile.weight },
  ];

  const handleAddToTimeline = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    // Only handle click if we're in timeline context
    if (!isTimelineContext) return;

    const index = parentNumber !== undefined ? parentNumber + 1 : 0;

    if (endPoint) {
      const confirm = window.confirm(
        "This is an endpoint. Are you sure you want to shift the timeline to this profile?"
      );
      if (confirm) {
        try {
          await dispatch(fetchTimelineTail({ 
            timelineNumber, 
            profileId: profile.id 
          })).unwrap();
          navigate(-1);
        } catch (error) {
          console.error("Failed to extend timeline:", error);
        }
      }
    } 
    else if (timeshift) {
      const confirm = window.confirm(
        "You are about to shift the timeline because the Timeline owner is no longer part of the path. Are you sure you want to proceed?"
      );
      if (confirm) {
        dispatch(addTimeline({
          timelineNumber: timelineNumber + 1,
          timelineOwner: profile.id
        }));
        navigate(`/timeline/${profile.id}`, {
          state: {
            currenttimelinenumber: timelineNumber + 1,
            currentlineowner: profile.id
          }
        });
      }
    }
    else if (parentNumber !== undefined) {
      const confirm = window.confirm(
        "You are about to shift the timeline path. Are you sure you want to proceed?"
      );
      if (confirm) {
        try {
          await dispatch(shiftTimelinePathThunk({
            timelineNumber,
            profileId: profile.id,
            index
          })).unwrap();
          navigate(-1);
        } catch (error) {
          console.error("Failed to shift timeline path:", error);
        }
      }
    }
  };

  const cycleProperty = (e: React.MouseEvent, direction: 'prev' | 'next') => {
    e.stopPropagation();
    setCurrentPropertyIndex(prev => {
      const total = properties.length;
      return direction === 'prev'
        ? (prev - 1 + total) % total
        : (prev + 1) % total;
    });
  };

  return (
    <div 
      className={`small-profile-card ${isTimelineContext ? 'clickable' : ''}`}
      onClick={isTimelineContext ? handleAddToTimeline : undefined}
    >
      <div className="small-profile-avatar-container">
        {profile.profilepic && !imageError ? (
          <img
            src={profile.profilepic}
            alt="Profile"
            className="small-profile-avatar"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="small-profile-avatar-placeholder">
            {profile.name.charAt(0)}
          </div>
        )}
      </div>

      <div className="small-profile-info-container">
        <div className="small-profile-name">{profile.name}</div>
        <div className="small-profile-id">ID: {profile.id}</div>

        <div className="small-profile-property-nav">
          <button
            className="small-profile-property-arrow"
            onClick={(e) => cycleProperty(e, 'prev')}
          >
            &lt;
          </button>

          <div className="small-profile-property-display">
            {properties[currentPropertyIndex].label}:{" "}
            {properties[currentPropertyIndex].value}
          </div>

          <button
            className="small-profile-property-arrow"
            onClick={(e) => cycleProperty(e, 'next')}
          >
            &gt;
          </button>
        </div>
      </div>
    </div>
  );
};

export default SmallProfile;