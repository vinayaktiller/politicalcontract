import React, { useEffect, useState } from 'react';
import './HeartbeatPage.css';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "../../../store";
import { 
  checkUserActivity, 
  markUserActive,
  fetchActivityHistory,
  invalidateCache,
  markActiveOptimistic // ✅ Import optimistic action
} from './heartbeatSlice';
import HeartbeatGraph from './HeartbeatGraph/HeartbeatGraph';
import { useNavigate } from 'react-router-dom';

const HeartbeatPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const heartbeatState = useSelector((state: RootState) => state.heartbeat);
  
  const {
    heartState,
    streak,
    lastActiveDate,
    status,
    error,
    activityHistory,
    historyStatus,
    historyError,
    lastFetched,
  } = heartbeatState;
  
  const userId = 11021801300001;
  const [hasInitialized, setHasInitialized] = useState(false);

  useEffect(() => {
    // ✅ Only run once on component mount OR when data becomes stale
    if (!hasInitialized || shouldRefetchData(lastFetched)) {
      console.log('Initializing or refreshing HeartbeatPage...');
      dispatch(checkUserActivity({ userId }));
      dispatch(fetchActivityHistory({ userId }));
      setHasInitialized(true);
    }
  }, [dispatch, userId, hasInitialized, lastFetched]);

  // ✅ Helper function to check if data should be refetched
  const shouldRefetchData = (lastFetched: string | null): boolean => {
    if (!lastFetched) return true;
    
    const lastFetchedDate = new Date(lastFetched);
    const now = new Date();
    
    // Refetch if it's a new day or data is older than 1 hour
    return !isSameDay(lastFetchedDate, now) || 
           (now.getTime() - lastFetchedDate.getTime()) > 60 * 60 * 1000;
  };

  // ✅ Helper to check if two dates are the same day
  const isSameDay = (date1: Date, date2: Date): boolean => {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
  };

  const handleMarkActive = async () => {
    if (heartState !== 'active' && heartState !== 'hyperactive') {
      // ✅ Immediate optimistic update for better UX
      dispatch(markActiveOptimistic());
      
      // Then make the actual API call
      try {
        await dispatch(markUserActive(userId)).unwrap();
      } catch (error) {
        // If API call fails, the state will be reverted by the rejected action
        console.error('Failed to mark active:', error);
      }
    }
  };

  const handleViewNetwork = () => {
    navigate('/heartbeat-network');
  };

  const handleRetry = () => {
    // ✅ Use force refresh to bypass cache
    dispatch(invalidateCache());
    dispatch(checkUserActivity({ userId, forceRefresh: true }));
    dispatch(fetchActivityHistory({ userId, forceRefresh: true }));
  };

  const handleForceRefresh = () => {
    // ✅ Manual refresh button for users with force refresh
    dispatch(invalidateCache());
    dispatch(checkUserActivity({ userId, forceRefresh: true }));
    dispatch(fetchActivityHistory({ userId, forceRefresh: true }));
  };

  const statusMessages = {
    inactive: "Your support is missed. Please contribute today!",
    passive: "You supported yesterday. Keep the momentum!",
    active: "Thank you for supporting the movement today!",
    hyperactive: "Amazing! Your daily support is fueling the movement!"
  };

  const getStreakInfo = () => {
    if (!lastActiveDate) return "No recent support";
    if (streak === 0) return "Start your support streak today!";
    if (streak === 1) return "Current streak: 1 day";
    if (streak >= 5) return `Current streak: ${streak} days! Keep going!`;
    return `Current streak: ${streak} days`;
  };

  const getHeartEmoji = () => {
    switch(heartState) {
      case 'inactive': return '🤍';
      case 'passive': return '❤️';
      case 'active': return '💓';
      case 'hyperactive': return '❤️‍🔥';
      default: return '🤍';
    }
  };

  const isLoading = status === 'loading' || historyStatus === 'loading';
  const showFireAnimation = heartState === 'hyperactive';
  const isHeartClickable = heartState !== 'active' && heartState !== 'hyperactive';
  const hasError = error || historyError;

  // If there's a major error, show a simple fallback
  if (error?.includes('permission') || error?.includes('not found')) {
    return (
      <div className="heartbeat-page">
        <div className="heartbeat-container">
          <div className="heartbeat-header">
            <h1 className="heartbeat-title">Movement Heartbeat</h1>
            <p className="heartbeat-subtitle">Keep the movement alive with your daily support</p>
          </div>
          
          <div className="heartbeat-visual inactive">
            <div className="heartbeat-emoji">❤️</div>
          </div>
          
          <div className="heartbeat-status">
            <p className="heartbeat-message">Welcome to Movement Heartbeat</p>
            <p className="heartbeat-streak">Click the heart to show your support!</p>
          </div>

          <div className="heartbeat-network-button-container">
            <button 
              className="heartbeat-network-button"
              onClick={handleViewNetwork}
            >
              View Network Activity
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="heartbeat-page">
      <div className="heartbeat-container">
        <div className="heartbeat-header">
          <h1 className="heartbeat-title">Movement Heartbeat</h1>
          <p className="heartbeat-subtitle">Keep the movement alive with your daily support</p>
          
          {/* ✅ Add manual refresh button */}
          <button 
            className="refresh-button"
            onClick={handleForceRefresh}
            disabled={isLoading}
            title="Force refresh data"
          >
            🔄 Refresh
          </button>
        </div>
        
        <div 
          className={`heartbeat-visual ${heartState} ${isHeartClickable ? 'clickable' : ''}`}
          onClick={isHeartClickable ? handleMarkActive : undefined}
        >
          <div className="heartbeat-emoji">
            {getHeartEmoji()}
            {showFireAnimation && (
              <div className="fire-effect">
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
                <div className="fire-particle"></div>
              </div>
            )}
          </div>
          {(heartState === 'active' || heartState === 'hyperactive') && (
            <>
              <div className="heartbeat-ripple"></div>
              <div className="heartbeat-ripple ripple-2"></div>
              <div className="heartbeat-ripple ripple-3"></div>
            </>
          )}
          {isHeartClickable && (
            <div className="heartbeat-click-prompt">
              Click to support!
            </div>
          )}
        </div>
        
        <div className="heartbeat-status">
          {isLoading ? (
            <div className="heartbeat-loading">
              <div className="heartbeat-spinner"></div>
              <p>Checking your status...</p>
            </div>
          ) : hasError ? (
            <div className="heartbeat-error-container">
              <p className="heartbeat-error">Unable to load status</p>
              <button className="retry-button" onClick={handleRetry}>
                Try Again
              </button>
            </div>
          ) : (
            <>
              <p className="heartbeat-message">{statusMessages[heartState]}</p>
              <p className="heartbeat-streak">{getStreakInfo()}</p>
            </>
          )}
        </div>

        {/* Network Button */}
        <div className="heartbeat-network-button-container">
          <button 
            className="heartbeat-network-button"
            onClick={handleViewNetwork}
            disabled={isLoading}
          >
            View Network Activity
          </button>
        </div>
        
        {historyStatus === 'loading' && (
          <div className="history-loading">
            <div className="heartbeat-spinner"></div>
            <p>Loading activity history...</p>
          </div>
        )}
        
        {historyStatus === 'succeeded' && (
          <>
            {activityHistory && activityHistory.length > 0 ? (
              <HeartbeatGraph activityHistory={activityHistory} />
            ) : (
              <p className="no-history-message">No activity history available yet.</p>
            )}
          </>
        )}

        {historyStatus === 'failed' && !isLoading && (
          <div className="heartbeat-error-container">
            <p className="heartbeat-error">Unable to load activity history</p>
            <button className="retry-button" onClick={handleRetry}>
              Try Again
            </button>
          </div>
        )}
        
      </div>
      
      <div className="heartbeat-footer">
        <p>Every contribution keeps the movement alive</p>
        <p>Join thousands supporting daily</p>
      </div>
    </div>
  );
};

export default HeartbeatPage;