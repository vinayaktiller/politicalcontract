import React, { useState, useEffect } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import SmallProfile from "./components/SmallProfile";
import { ProfileData, RelationProfile } from "../Timelinepage/timelineTypes";
import api from "../../../api";
import "./css/ChildrenPage.css";


interface LocationState {
  profileData?: ProfileData;
  timelineNumber?: number;
  timeshift?: boolean;
  parentNumber?: number;
  endPoint?: boolean;
}


type SortableAttribute = "influence" | "depth" | "weight" | "childcount";


const ConnectionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get current user ID from localStorage
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  const locationState = (location.state as LocationState) || {};
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [profilesPerPage, setProfilesPerPage] = useState(6);
  const [imageError, setImageError] = useState(false); // NEW: fallback state
  
  const {
    profileData: initialProfileData,
    timelineNumber: initialTimelineNumber = 1,
    timeshift: initialTimeshift = false,
    parentNumber: initialParentNumber,
    endPoint: initialEndPoint = false
  } = locationState;

  const [profileData, setProfileData] = useState<ProfileData | null>(initialProfileData || null);
  const [connections, setConnections] = useState<RelationProfile[]>(initialProfileData?.connections || []);
  const [loading, setLoading] = useState(!initialProfileData);
  const [timelineNumber, setTimelineNumber] = useState(initialTimelineNumber);
  const [timeshift, setTimeshift] = useState(initialTimeshift);
  const [parentNumber, setParentNumber] = useState(initialParentNumber);
  const [endPoint, setEndPoint] = useState(initialEndPoint);
  
  // Determine if we're in timeline context
  const isTimelineContext = !!initialProfileData;

  useEffect(() => {
    // Set current user ID from localStorage
    const userId = localStorage.getItem("user_id");
    setCurrentUserId(userId);
  }, []);

  useEffect(() => {
    const fetchProfileData = async () => {
      setLoading(true);
      try {
        const response = await api.get<ProfileData>(
          `/api/users/timeline/tail/${id}/`
        );
        
        setProfileData(response.data);
        setConnections(response.data.connections || []);
        
        // Set default values if not provided via state
        if (initialTimelineNumber === 1) setTimelineNumber(1);
        if (initialTimeshift === false) setTimeshift(false);
        if (initialEndPoint === false) setEndPoint(false);

        setImageError(false); // reset error if profile changes
      } catch (error) {
        console.error("Error fetching profile data:", error);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch if not provided via navigation state
    if (!initialProfileData && id) {
      fetchProfileData();
    }
  }, [id, initialProfileData, initialTimelineNumber, initialTimeshift, initialEndPoint]);

  useEffect(() => {
    const updateProfilesPerPage = () => {
      setProfilesPerPage(window.innerHeight >= 700 ? 8 : 6);
    };

    updateProfilesPerPage();
    window.addEventListener("resize", updateProfilesPerPage);
    return () => window.removeEventListener("resize", updateProfilesPerPage);
  }, []);

  const sortProfiles = (attribute: SortableAttribute, order: "asc" | "desc") => {
    const sorted = [...connections].sort((a, b) => {
      const aVal = a[attribute] as number;
      const bVal = b[attribute] as number;
      return order === "asc" ? aVal - bVal : bVal - aVal;
    });
    setConnections(sorted);
  };

  const navigateToChildren = () => {
    if (!profileData) return;
    
    navigate(`/children/${profileData.id}`, {
      state: {
        profileData,
        timelineNumber,
        parentNumber,
        timeshift,
        endPoint
      }
    });
  };

  // Navigate to make connections page
  const navigateToMakeConnections = () => {
    navigate('/make-connections');
  };

  const totalPages = Math.ceil(connections.length / profilesPerPage);
  const paginatedProfiles = connections.slice(
    (currentPage - 1) * profilesPerPage,
    currentPage * profilesPerPage
  );

  const goToNextPage = () => currentPage < totalPages && setCurrentPage(p => p + 1);
  const goToPrevPage = () => currentPage > 1 && setCurrentPage(p => p - 1);

  if (loading) return <div className="children-page-loading">Loading profile data...</div>;
  if (!profileData) return <div className="children-page-error">No profile data available</div>;

  return (
    <div className="children-page-container">
      <div className="children-page-main-profile-container">
        <div className="children-page-main-profile-container-left">
          {profileData.profilepic && !imageError ? (
            <img 
              src={profileData.profilepic} 
              alt="Profile" 
              className="children-page-main-profile-pic"
              onError={() => setImageError(true)} // NEW: fallback trigger
            />
          ) : (
            <div className="children-page-main-profile-pic-placeholder">
              {profileData.name ? profileData.name.charAt(0) : '?'}
            </div>
          )}
        </div>
        <div className="children-page-main-profile-container-right">
          <div className="children-page-main-profile-details">
            <p>ID: {profileData.id}</p>
            <p>Name: {profileData.name || 'Unknown'}</p>
            <p>Connections: {connections.length}</p>
           
            {parentNumber !== undefined && <p>Parent Number: {parentNumber}</p>}
            
            {/* Moved Make Connections button here for better UI placement */}
            {id === currentUserId && (
              <button 
                className="children-page-make-connections-btn"
                onClick={navigateToMakeConnections}
              >
                Make Connections
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="children-page-controls">
        <div className="children-page-sort-section">
          <div className="children-page-custom-dropdown">
            <button 
              className="children-page-dropdown-button"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              Sort By
            </button>
            {dropdownOpen && (
              <div className="children-page-dropdown-menu">
                <button onClick={() => { sortProfiles('childcount', 'asc'); setDropdownOpen(false); }}>
                  Children Count (Asc)
                </button>
                <button onClick={() => { sortProfiles('childcount', 'desc'); setDropdownOpen(false); }}>
                  Children Count (Desc)
                </button>
                <button onClick={() => { sortProfiles('influence', 'asc'); setDropdownOpen(false); }}>
                  Influence (Asc)
                </button>
                <button onClick={() => { sortProfiles('influence', 'desc'); setDropdownOpen(false); }}>
                  Influence (Desc)
                </button>
                <button onClick={() => { sortProfiles('depth', 'asc'); setDropdownOpen(false); }}>
                  Depth (Asc)
                </button>
                <button onClick={() => { sortProfiles('depth', 'desc'); setDropdownOpen(false); }}>
                  Depth (Desc)
                </button>
                <button onClick={() => { sortProfiles('weight', 'asc'); setDropdownOpen(false); }}>
                  Weight (Asc)
                </button>
                <button onClick={() => { sortProfiles('weight', 'desc'); setDropdownOpen(false); }}>
                  Weight (Desc)
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="children-page-connections-section">
          <button 
            className="children-page-connections-button"
            onClick={navigateToChildren}
          >
            View Children
          </button>
        </div>
      </div>

      <div className="children-page-profiles-container">
        {paginatedProfiles.length > 0 ? (
          paginatedProfiles.map((profile) => (
            <SmallProfile
              key={profile.id}
              profile={profile}
              timelineNumber={timelineNumber}
              parentNumber={parentNumber}
              timeshift={timeshift}
              endPoint={endPoint}
              isTimelineContext={isTimelineContext}
            />
          ))
        ) : (
          <div className="children-page-no-profiles-message">
            No connections available
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="children-page-pagination-controls">
          <button 
            onClick={goToPrevPage}
            disabled={currentPage === 1}
            className="children-page-pagination-button"
          >
            ← Previous
          </button>
          
          <span className="children-page-indicator">
            Page {currentPage} of {totalPages}
          </span>
          
          <button 
            onClick={goToNextPage}
            disabled={currentPage === totalPages}
            className="children-page-pagination-button"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};


export default ConnectionPage;
