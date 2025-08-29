// import React, { useState, useEffect, useRef } from 'react';
// import { useLocation, useNavigate } from "react-router-dom";
// import { useDispatch, useSelector } from 'react-redux';
// import type { AppDispatch, RootState } from "../../../store";
// import { fetchUserMilestones, invalidateMilestoneCache } from './milestonesSlice';
// import './MilestonePage.css';

// const initialState = {
//   milestones: [],
//   status: 'idle',
//   error: null,
//   lastUpdated: null
// };

// const MilestonePage: React.FC = () => {
//   const dispatch = useDispatch<AppDispatch>();
//   const location = useLocation();
//   const navigate = useNavigate();

//   // Detect if navigation came from celebration modal
//   const [isFromCelebration, setIsFromCelebration] = useState(false);

//   // Animation refs and state
//   const [transitionData, setTransitionData] = useState<any>(null);
//   const highlightedCardRef = useRef<HTMLDivElement>(null);
//   const [showClone, setShowClone] = useState(false);
//   const cloneRef = useRef<HTMLDivElement>(null);
//   const milestoneListRef = useRef<HTMLDivElement>(null);

//   // Use a timeout to ensure DOM is ready before scrolling
//   const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

//   // Redux selectors
//   const milestoneState = useSelector((state: RootState) => state.milestones || initialState);
//   const { milestones, status, error } = milestoneState;
//   const isConnected = useSelector((state: RootState) => state.notifications.isConnected);

//   // View mode and filter state
//   const [viewMode, setViewMode] = useState<'detail' | 'gallery'>('detail');
//   const [filterType, setFilterType] = useState<string>('all');

//   // Highlighted milestone ID from URL query param
//   const [highlightedId, setHighlightedId] = useState<number | null>(null);

//   useEffect(() => {
//     // Detect if arrived via celebration modal navigation
//     if (location.state?.fromCelebration) {
//       setIsFromCelebration(true);
//     } else {
//       setIsFromCelebration(false);
//     }

//     if (location.state?.celebrationData) {
//       setTransitionData(location.state.celebrationData);
//     }
//   }, [location]);

//   useEffect(() => {
//     const storedId = localStorage.getItem("user_id");
//     if (!storedId) return;

//     const userId = parseInt(storedId, 10);
//     dispatch(invalidateMilestoneCache());

//     if (status === 'idle' && isConnected) {
//       dispatch(fetchUserMilestones(userId));
//     }
//   }, [dispatch, status, isConnected]);

//   useEffect(() => {
//     const params = new URLSearchParams(location.search);
//     const highlightId = params.get('highlight');

//     if (highlightId) {
//       const id = parseInt(highlightId, 10);
//       if (!isNaN(id)) {
//         setHighlightedId(id);

//         if (transitionData && !showClone) {
//           setShowClone(true);
//           setTimeout(() => {
//             if (cloneRef.current) {
//               cloneRef.current.classList.add('animate-dissolve');
//               setTimeout(() => {
//                 setShowClone(false);
//                 setTransitionData(null);
//               }, 1000);
//             }
//           }, 50);
//         }

//         setTimeout(() => {
//           setHighlightedId(null);
//         }, 3000);
//       }
//     }

//   }, [location.search, transitionData, showClone]);

//   useEffect(() => {
//     if (showClone && highlightedCardRef.current && cloneRef.current) {
//       console.log('Animating clone');
//       const targetRect = highlightedCardRef.current.getBoundingClientRect();
//       const clone = cloneRef.current;
//       clone.style.setProperty('--target-top', `${targetRect.top}px`);
//       clone.style.setProperty('--target-left', `${targetRect.left}px`);
//       clone.style.setProperty('--target-width', `${targetRect.width}px`);
//       clone.style.setProperty('--target-height', `${targetRect.height}px`);
//     }
//   }, [showClone]);

//   // Smooth scroll on mount or when highlightedId changes with null checks and console log
//   useEffect(() => {
//     const container = milestoneListRef.current;
//     console.log("Current URL:", location.pathname + location.search + location.hash);
//     if (!container) return;

//     // Clear previous timeout if any
//     if (scrollTimeoutRef.current) {
//       clearTimeout(scrollTimeoutRef.current);
//     }

//     scrollTimeoutRef.current = setTimeout(() => {
//       let card: HTMLElement | null = null;

//       if (isFromCelebration && highlightedCardRef.current) {
//         card = highlightedCardRef.current;
//       } else if (highlightedId) {
//         console.log("Looking for card with ID:", highlightedId);
//         card = document.getElementById(`/milestones?highlight=${highlightedId}`) as HTMLElement;
//         console.log("Found card:", card);
//       }

//       if (location.pathname === "/milestones" && !location.search) {
//         const scrollTop = 0;
//         container.scrollTo({ top: scrollTop > 0 ? scrollTop : 0, behavior: 'smooth' });
//         console.log("Scrolling container to top: 0");
        
//       } else {
//         console.log("Found highlighted card:", card);
//         const scrollTop = 200;
//         container.scrollTo({ top: scrollTop > 0 ? scrollTop : 0, behavior: 'smooth' });
//         console.log("Scrolling container to:", scrollTop > 0 ? scrollTop : 0);
//       }

//       setIsFromCelebration(false);
//     }, 150);

//     return () => {
//       if (scrollTimeoutRef.current) {
//         clearTimeout(scrollTimeoutRef.current);
//       }
//     };
//   }, [isFromCelebration, highlightedId]);

//   const safeMilestones = milestones || [];

//   const sortedMilestones = [...safeMilestones].sort((a, b) => {
//     if (a.id === highlightedId) return -1;
//     if (b.id === highlightedId) return 1;
//     return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
//   });


//   const filteredMilestones = filterType === 'all'
//     ? sortedMilestones
//     : sortedMilestones.filter(m => m.type === filterType);

//   if (status === 'loading') {
//     return (
//       <div className="milestone-page-container" ref={milestoneListRef}>
//         <div className="milestone-page-loader"></div>
//         <p>Retrieving your achievements...</p>
//       </div>
//     );
//   }


//   if (error) {
//     return (
//       <div className="milestone-page-container" ref={milestoneListRef}>
//         <div className="milestone-page-error">
//           <h3>Error</h3>
//           <p>{error}</p>
//         </div>
//       </div>
//     );
//   }


//   return (
//     <div className="milestone-page-container" ref={milestoneListRef}>
//       <div className="milestone-page-header">
//         <h1>Your Achievement Gallery</h1>
//         <p>Recognized milestones for your contributions</p>


//         <div className="view-controls">
//           <button
//             className={`view-button ${viewMode === 'detail' ? 'active' : ''}`}
//             onClick={() => setViewMode('detail')}
//           >Detail View</button>
//           <button
//             className={`view-button ${viewMode === 'gallery' ? 'active' : ''}`}
//             onClick={() => setViewMode('gallery')}
//           >Photo Gallery</button>


//           {viewMode === 'gallery' && (
//             <div className="type-filter">
//               <label htmlFor="type-filter">Filter by type:</label>
//               <select
//                 id="type-filter"
//                 value={filterType}
//                 onChange={(e) => setFilterType(e.target.value)}
//               >
//                 <option value="all">All Types</option>
//                 <option value="initiation">Initiation</option>
//                 <option value="influence">Influence</option>
//               </select>
//             </div>
//           )}
//         </div>
//       </div>


//       {safeMilestones.length === 0 ? (
//         <div className="milestone-page-empty">
//           <div className="milestone-page-empty-icon">🏆</div>
//           <h3>No Milestones Yet</h3>
//           <p>Continue building your network to earn achievements!</p>
//         </div>
//       ) : viewMode === 'detail' ? (
//         <div className="milestone-grid">
//           {sortedMilestones.map(milestone => {
//             const imgUrl = `http://localhost:3000/${milestone.type}/${milestone.photo_id}.jpg`;
//             const badgeClass = `milestone-badge milestone-badge-${milestone.type}`;
//             const isHighlighted = highlightedId === milestone.id;
//              const handleWriteInsight = () => {
//                 const insightData = {
//                   milestone_id: milestone.milestone_id,
//                   user_id: milestone.user_id,
//                   title: milestone.title,
//                   text: milestone.text,
//                   created_at: milestone.created_at,
//                   type: milestone.type,
//                   photo_id: milestone.photo_id,
//                   milestone_kind: "milestone", // to identify in BlogCreator
//                 };
//                 console.log("📝 Navigating to BlogCreator with milestone insight:", insightData);
//                 navigate("/blog-creator", { state: insightData });
//               };


//             return (
//               <div
//                 key={milestone.id}
//                 id={`milestone-${milestone.id}`}
//                 ref={isHighlighted ? highlightedCardRef : null}
//                 className={`milestone-card ${isHighlighted ? 'highlight-pulse' : ''}`}
//               >
//                 <div className="card-top-section">
//                   <div className={badgeClass}>For: {milestone.type}</div>
//                 </div>


//                 <div className="milestone-image-container">
//                   <img
//                     src={imgUrl}
//                     alt={milestone.title}
//                     className="milestone-image"
//                     onError={e => {
//                       (e.target as HTMLImageElement).src = `http://localhost:3000/initiation/1.jpg`;
//                     }}
//                   />
//                 </div>


//                 <div className="milestone-content">
//                   <h3 className="milestone-title">{milestone.title.toUpperCase()}</h3>
//                   <p className="milestone-description">{milestone.text}</p>
//                   <div className="milestone-date">
//                     Awarded on {new Date(milestone.created_at).toLocaleDateString()}
//                   </div>
//                   <button
//                   className="milestone-write-insight-button"
//                   onClick={handleWriteInsight}
//                 >
//                   blog
//                 </button>
//                 </div>
//               </div>
//             );
//           })}
//         </div>
//       ) : (
//         <div className="gallery-grid">
//           {filteredMilestones.map(milestone => {
//             const imgUrl = `http://localhost:3000/${milestone.type}/${milestone.photo_id}.jpg`;


//             return (
//               <div key={milestone.id} className="gallery-item">
//                 <div className="gallery-image-container">
//                   <img
//                     src={imgUrl}
//                     alt={milestone.title}
//                     className="gallery-image"
//                     onError={e => {
//                       (e.target as HTMLImageElement).src = `http://localhost:3000/initiation/1.jpg`;
//                     }}
//                   />
//                 </div>
//                 <div className="gallery-caption">
//                   <span className="gallery-type">{milestone.title}</span>
//                 </div>
//               </div>
//             );
//           })}
//         </div>
//       )}


//       {showClone && transitionData && (
//         <div
//           ref={cloneRef}
//           className="celebration-clone"
//           style={{
//             position: 'fixed',
//             top: `${transitionData.startRect.top}px`,
//             left: `${transitionData.startRect.left}px`,
//             width: `${transitionData.startRect.width}px`,
//             height: `${transitionData.startRect.height}px`,
//             backgroundImage: `url(${transitionData.imageUrl})`,
//             backgroundSize: 'cover',
//             backgroundPosition: 'center',
//             borderRadius: '8px',
//             border: '3px solid white',
//             boxShadow: '0 0 30px rgba(255, 215, 0, 0.8)',
//             zIndex: 2000,
//           }}
//         />
//       )}
//     </div>
//   );
// };

// export default MilestonePage;


import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../store";
import { fetchUserMilestones, invalidateMilestoneCache } from './milestonesSlice';
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

  useEffect(() => {
    if (location.state?.fromCelebration) {
      setIsFromCelebration(true);
    } else {
      setIsFromCelebration(false);
    }

    if (location.state?.celebrationData) {
      setTransitionData(location.state.celebrationData);
    }
  }, [location]);

  useEffect(() => {
    const storedId = localStorage.getItem("user_id");
    if (!storedId) return;

    const userId = parseInt(storedId, 10);
    dispatch(invalidateMilestoneCache());

    if (status === 'idle' && isConnected) {
      dispatch(fetchUserMilestones(userId));
    }
  }, [dispatch, status, isConnected]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const highlightId = params.get('highlight');

    if (highlightId) {
      const id = parseInt(highlightId, 10);
      if (!isNaN(id)) {
        setHighlightedId(id);

        if (transitionData && !showClone) {
          setShowClone(true);
          setTimeout(() => {
            if (cloneRef.current) {
              cloneRef.current.classList.add('animate-dissolve');
              setTimeout(() => {
                setShowClone(false);
                setTransitionData(null);
              }, 1000);
            }
          }, 50);
        }

        setTimeout(() => {
          setHighlightedId(null);
        }, 3000);
      }
    }

  }, [location.search, transitionData, showClone]);

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

  useEffect(() => {
    const container = milestoneListRef.current;
    if (!container) return;

    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    scrollTimeoutRef.current = setTimeout(() => {
      let card: HTMLElement | null = null;

      if (isFromCelebration && highlightedCardRef.current) {
        card = highlightedCardRef.current;
      } else if (highlightedId) {
        card = document.getElementById(`milestone-${highlightedId}`) as HTMLElement;
      }

      if (location.pathname === "/milestones" && !location.search) {
        container.scrollTo({ top: 0, behavior: 'smooth' });
      } else if (card) {
        // Scroll so the card is visible (offset can be adjusted)
        const containerRect = container.getBoundingClientRect();
        const cardRect = card.getBoundingClientRect();
        const offset = cardRect.top - containerRect.top - 20; // 20px padding
        container.scrollTo({ top: offset, behavior: 'smooth' });
      }

      setIsFromCelebration(false);
    }, 150);

    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [isFromCelebration, highlightedId, location.pathname, location.search]);

  // FIX: ensure milestones is always an array
  const safeMilestones = Array.isArray(milestones) ? milestones : [];

  const sortedMilestones = [...safeMilestones].sort((a, b) => {
    if (a.id === highlightedId) return -1;
    if (b.id === highlightedId) return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const filteredMilestones = filterType === 'all'
    ? sortedMilestones
    : sortedMilestones.filter(m => m.type === filterType);

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
          <h3>Error</h3>
          <p>{typeof error === 'string' ? error : JSON.stringify(error)}</p>
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
          >Detail View</button>
          <button
            className={`view-button ${viewMode === 'gallery' ? 'active' : ''}`}
            onClick={() => setViewMode('gallery')}
          >Photo Gallery</button>

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
        </div>
      ) : viewMode === 'detail' ? (
        <div className="milestone-grid">
          {sortedMilestones.map(milestone => {
            const imgUrl = `http://localhost:3000/${milestone.type}/${milestone.photo_id}.jpg`;
            const badgeClass = `milestone-badge milestone-badge-${milestone.type}`;
            const isHighlighted = highlightedId === milestone.id;
            
            const handleWriteInsight = () => {
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
            };

            return (
              <div
                key={milestone.id}
                id={`milestone-${milestone.id}`}
                ref={isHighlighted ? highlightedCardRef : null}
                className={`milestone-card ${isHighlighted ? 'highlight-pulse' : ''}`}
              >
                <div className="card-top-section">
                  <div className={badgeClass}>For: {milestone.type}</div>
                </div>

                <div className="milestone-image-container">
                  <img
                    src={imgUrl}
                    alt={milestone.title}
                    className="milestone-image"
                    onError={e => {
                      (e.target as HTMLImageElement).src = `http://localhost:3000/initiation/1.jpg`;
                    }}
                  />
                </div>

                <div className="milestone-content">
                  <h3 className="milestone-title">{milestone.title.toUpperCase()}</h3>
                  <p className="milestone-description">{milestone.text}</p>
                  <div className="milestone-date">
                    Awarded on {new Date(milestone.created_at).toLocaleDateString()}
                  </div>
                  <button
                    className="milestone-write-insight-button"
                    onClick={handleWriteInsight}
                  >
                    blog
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="gallery-grid">
          {filteredMilestones.map(milestone => {
            const imgUrl = `http://localhost:3000/${milestone.type}/${milestone.photo_id}.jpg`;

            return (
              <div key={milestone.id} className="gallery-item">
                <div className="gallery-image-container">
                  <img
                    src={imgUrl}
                    alt={milestone.title}
                    className="gallery-image"
                    onError={e => {
                      (e.target as HTMLImageElement).src = `http://localhost:3000/initiation/1.jpg`;
                    }}
                  />
                </div>
                <div className="gallery-caption">
                  <span className="gallery-type">{milestone.title}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showClone && transitionData && (
        <div
          ref={cloneRef}
          className="celebration-clone"
          style={{
            position: 'fixed',
            top: `${transitionData.startRect.top}px`,
            left: `${transitionData.startRect.left}px`,
            width: `${transitionData.startRect.width}px`,
            height: `${transitionData.startRect.height}px`,
            backgroundImage: `url(${transitionData.imageUrl})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            borderRadius: '8px',
            border: '3px solid white',
            boxShadow: '0 0 30px rgba(255, 215, 0, 0.8)',
            zIndex: 2000,
          }}
        />
      )}
    </div>
  );
};

export default MilestonePage;
