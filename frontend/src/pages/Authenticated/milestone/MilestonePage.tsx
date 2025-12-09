import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../store";
import { fetchUserMilestones, invalidateMilestoneCache } from './milestonesSlice';
import { config } from '../../Unauthenticated/config';
import './MilestonePage.css';

const initialState = {
  milestones: [],
  status: 'idle',
  error: null,
  lastUpdated: null
};

const MilestonePage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const location = useLocation();
  const navigate = useNavigate();

  const [isFromCelebration, setIsFromCelebration] = useState(false);
  const [transitionData, setTransitionData] = useState<any>(null);
  const highlightedCardRef = useRef<HTMLDivElement>(null);
  const [showClone, setShowClone] = useState(false);
  const cloneRef = useRef<HTMLDivElement>(null);
  const milestoneListRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const milestoneState = useSelector((state: RootState) => state.milestones || initialState);
  const { milestones, status, error } = milestoneState;
  const isConnected = useSelector((state: RootState) => state.notifications.isConnected);

  const [viewMode, setViewMode] = useState<'detail' | 'gallery'>('detail');
  const [filterType, setFilterType] = useState<string>('all');
  const [highlightedId, setHighlightedId] = useState<number | null>(null);
  const [hasFetched, setHasFetched] = useState(false);
  const [forceRefetch, setForceRefetch] = useState(false);

  const FRONTEND_BASE_URL = config.FRONTEND_BASE_URL;

  // Handle celebration transition
  useEffect(() => {
    if (location.state?.fromCelebration) {
      setIsFromCelebration(true);
      // Clear celebration state after processing
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  useEffect(() => {
    if (location.state?.celebrationData) {
      setTransitionData(location.state.celebrationData);
    }
  }, [location]);

  // Fetch milestones - improved logic
  const fetchMilestones = useCallback(() => {
    const storedId = localStorage.getItem("user_id");
    if (!storedId) {
      console.error("No user_id found in localStorage");
      return;
    }

    const userId = parseInt(storedId, 10);
    if (isNaN(userId)) {
      console.error("Invalid user_id in localStorage:", storedId);
      return;
    }

    console.log("Fetching milestones for user:", userId);
    
    dispatch(invalidateMilestoneCache());
    dispatch(fetchUserMilestones(userId))
      .unwrap()
      .then(() => {
        setHasFetched(true);
        setForceRefetch(false);
        console.log("Milestones fetched successfully");
      })
      .catch((err) => {
        console.error("Failed to fetch milestones:", err);
      });
  }, [dispatch]);

  // Initial fetch and refetch when connection is restored
  useEffect(() => {
    if (!hasFetched || forceRefetch || (isConnected && status === 'idle')) {
      fetchMilestones();
    }
  }, [hasFetched, forceRefetch, isConnected, status, fetchMilestones]);

  // Force fetch on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMilestones();
    }, 100);

    return () => clearTimeout(timer);
  }, [fetchMilestones]);

  // Handle highlight from URL
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const highlightId = params.get('highlight');

    if (highlightId) {
      const id = parseInt(highlightId, 10);
      if (!isNaN(id)) {
        setHighlightedId(id);

        // If we have transition data, show clone animation
        if (transitionData && !showClone) {
          setShowClone(true);
          
          // Start animation after a short delay
          setTimeout(() => {
            if (cloneRef.current) {
              cloneRef.current.classList.add('animate-dissolve');
              setTimeout(() => {
                setShowClone(false);
                setTransitionData(null);
              }, 800); // Match CSS animation duration
            }
          }, 50);
        }

        // Clear highlight after animation
        setTimeout(() => {
          setHighlightedId(null);
          // Clean URL without refresh
          navigate('/milestones', { replace: true });
        }, 3000);
      }
    }
  }, [location.search, transitionData, showClone, navigate]);

  // Position clone for animation
  useEffect(() => {
    if (showClone && highlightedCardRef.current && cloneRef.current) {
      const targetRect = highlightedCardRef.current.getBoundingClientRect();
      const clone = cloneRef.current;
      clone.style.setProperty('--target-top', `${targetRect.top}px`);
      clone.style.setProperty('--target-left', `${targetRect.left}px`);
      clone.style.setProperty('--target-width', `${targetRect.width}px`);
      clone.style.setProperty('--target-height', `${targetRect.height}px`);
    }
  }, [showClone]);

  // Scroll to highlighted card
  useEffect(() => {
    const container = milestoneListRef.current;
    if (!container) return;

    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    scrollTimeoutRef.current = setTimeout(() => {
      let card: HTMLElement | null = null;

      if (highlightedId) {
        card = document.getElementById(`milestone-${highlightedId}`) as HTMLElement;
      }

      if (card) {
        const containerRect = container.getBoundingClientRect();
        const cardRect = card.getBoundingClientRect();
        const offset = cardRect.top - containerRect.top - 20;
        container.scrollTo({ top: offset, behavior: 'smooth' });
      }

      setIsFromCelebration(false);
    }, 300);

    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [highlightedId, isFromCelebration]);

  // Ensure milestones is always an array
  const safeMilestones = Array.isArray(milestones) ? milestones : [];

  // Sort milestones: highlighted first, then by date (newest first)
  const sortedMilestones = [...safeMilestones].sort((a, b) => {
    if (a.id === highlightedId) return -1;
    if (b.id === highlightedId) return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  // Filter milestones for gallery view
  const filteredMilestones = filterType === 'all'
    ? sortedMilestones
    : sortedMilestones.filter(m => m.type === filterType);

  // Handle retry
  const handleRetry = useCallback(() => {
    setForceRefetch(true);
  }, []);

  // Handle write insight
  const handleWriteInsight = useCallback((milestone: any) => {
    const insightData = {
      milestone_id: milestone.id,
      user_id: milestone.user_id,
      title: milestone.title,
      text: milestone.text,
      created_at: milestone.created_at,
      type: milestone.type,
      photo_id: milestone.photo_id,
      milestone_kind: "milestone",
    };
    navigate("/blog-creator", { state: insightData });
  }, [navigate]);

  if (status === 'loading') {
    return (
      <div className="milestone-page-container" ref={milestoneListRef}>
        <div className="milestone-page-loader"></div>
        <p>Retrieving your achievements...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="milestone-page-container" ref={milestoneListRef}>
        <div className="milestone-page-error">
          <h3>Error Loading Milestones</h3>
          <p>{typeof error === 'string' ? error : 'Failed to load milestones'}</p>
          <button onClick={handleRetry} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="milestone-page-container" ref={milestoneListRef}>
      <div className="milestone-page-header">
        <h1>Your Achievement Gallery</h1>
        <p>Recognized milestones for your contributions</p>

        <div className="view-controls">
          <button
            className={`view-button ${viewMode === 'detail' ? 'active' : ''}`}
            onClick={() => setViewMode('detail')}
          >
            Detail View
          </button>
          <button
            className={`view-button ${viewMode === 'gallery' ? 'active' : ''}`}
            onClick={() => setViewMode('gallery')}
          >
            Photo Gallery
          </button>

          {viewMode === 'gallery' && (
            <div className="type-filter">
              <label htmlFor="type-filter">Filter by type:</label>
              <select
                id="type-filter"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="initiation">Initiation</option>
                <option value="influence">Influence</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {safeMilestones.length === 0 ? (
        <div className="milestone-page-empty">
          <div className="milestone-page-empty-icon">🏆</div>
          <h3>No Milestones Yet</h3>
          <p>Continue building your network to earn achievements!</p>
          <button onClick={handleRetry} className="retry-button">
            Check for New Milestones
          </button>
        </div>
      ) : viewMode === 'detail' ? (
        <div className="milestone-grid">
          {sortedMilestones.map((milestone) => {
            const imgUrl = milestone.photo_url || 
              (milestone.type && milestone.photo_id 
                ? `${FRONTEND_BASE_URL}/${milestone.type}/${milestone.photo_id}.jpg`
                : `${FRONTEND_BASE_URL}/initiation/1.jpg`);
            
            const badgeClass = `milestone-badge milestone-badge-${milestone.type || 'initiation'}`;
            const isHighlighted = highlightedId === milestone.id;
            
            return (
              <div
                key={milestone.id}
                id={`milestone-${milestone.id}`}
                ref={isHighlighted ? highlightedCardRef : null}
                className={`milestone-card ${isHighlighted ? 'highlight-pulse' : ''}`}
              >
                <div className="card-top-section">
                  <div className={badgeClass}>
                    For: {milestone.type || 'milestone'}
                  </div>
                </div>

                <div className="milestone-image-container">
                  <img
                    src={imgUrl}
                    alt={milestone.title}
                    className="milestone-image"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `${FRONTEND_BASE_URL}/initiation/1.jpg`;
                    }}
                  />
                </div>

                <div className="milestone-content">
                  <h3 className="milestone-title">
                    {milestone.title ? milestone.title.toUpperCase() : 'MILESTONE'}
                  </h3>
                  <p className="milestone-description">
                    {milestone.text || 'Congratulations on your achievement!'}
                  </p>
                  <div className="milestone-date">
                    Awarded on {new Date(milestone.created_at).toLocaleDateString()}
                  </div>
                  <button
                    className="milestone-write-insight-button"
                    onClick={() => handleWriteInsight(milestone)}
                  >
                    Write Insight
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="gallery-grid">
          {filteredMilestones.map((milestone) => {
            const imgUrl = milestone.photo_url || 
              (milestone.type && milestone.photo_id 
                ? `${FRONTEND_BASE_URL}/${milestone.type}/${milestone.photo_id}.jpg`
                : `${FRONTEND_BASE_URL}/initiation/1.jpg`);
            
            return (
              <div key={milestone.id} className="gallery-item">
                <div className="gallery-image-container">
                  <img
                    src={imgUrl}
                    alt={milestone.title}
                    className="gallery-image"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `${FRONTEND_BASE_URL}/initiation/1.jpg`;
                    }}
                  />
                </div>
                <div className="gallery-caption">
                  <span className="gallery-type">
                    {milestone.title || 'Milestone'}
                  </span>
                  <span className="gallery-date">
                    {new Date(milestone.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* {showClone && transitionData && (
        <div
          ref={cloneRef}
          className="celebration-clone"
          style={{
            position: 'fixed',
            top: transitionData.startRect?.top || '50%',
            left: transitionData.startRect?.left || '50%',
            width: transitionData.startRect?.width || '300px',
            height: transitionData.startRect?.height || '300px',
            backgroundImage: `url(${transitionData.imageUrl})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            borderRadius: '8px',
            border: '3px solid white',
            boxShadow: '0 0 30px rgba(255, 215, 0, 0.8)',
            zIndex: 9999,
          }}
        />
      )} */}
    </div>
  );
};

export default MilestonePage;